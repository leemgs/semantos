"""
safety_core.py — conformal safety primitives for the SemantOS safety runtime.

Dependency-light (numpy only) re-implementation of the same math validated by the
offline reproduction harness (reproduce/conformal.py, reproduce/adwin.py), so the
*live* service gates on identically-derived thresholds:

  * conformal_threshold : split-conformal veto threshold at miscoverage alpha.
  * select_tau_by_cost  : operating tau minimising expected mis-veto cost C(tau).
  * ADWIN               : streaming drift detector over the uncertainty signal.
  * SlidingCalibrator   : maintains D_cal, recalibrates tau on drift / on schedule.

A calibration record is (u, unsafe) where u in [0,1] is the reasoner's reported
uncertainty and `unsafe` is whether the applied action actually breached the SLO.
"""
from __future__ import annotations

import math
from collections import deque

import numpy as np


def conformal_threshold(u, y, alpha: float) -> float:
    """Split-conformal veto threshold.

    Nonconformity of an *unsafe* action is (1 - u): unsafe actions should score
    high u.  We take the empirical (1-alpha) quantile over unsafe scores with the
    standard finite-sample correction, giving a threshold tau such that, under
    exchangeability, the probability an unsafe action is *not* vetoed is <= alpha.
    """
    u = np.asarray(u, float)
    y = np.asarray(y, bool)
    unsafe = u[y]
    if unsafe.size == 0:
        return 0.5
    n = unsafe.size
    q = min(1.0, math.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(unsafe, 1 - q, method="lower"))


def rollback_precision_recall(u, y, tau: float):
    u = np.asarray(u, float)
    y = np.asarray(y, bool)
    vetoed = u >= tau
    tp = int(np.sum(vetoed & y))
    fp = int(np.sum(vetoed & ~y))
    fn = int(np.sum(~vetoed & y))
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return precision, recall


def select_tau_by_cost(u, y, dslo_of_tau, cost: dict, grid=None) -> float:
    """Pick tau minimising C(tau)=c_fn*FN + c_fp*FP + lam*SLO_debt(tau).

    FN = unsafe action let through (expensive); FP = safe action needlessly
    vetoed; SLO_debt grows as tau rises (more conservative -> more missed wins).
    """
    u = np.asarray(u, float)
    y = np.asarray(y, bool)
    if grid is None:
        grid = np.round(np.arange(0.30, 0.86, 0.01), 2)
    n = max(1, u.size)
    best_tau, best_c = 0.55, math.inf
    for tau in grid:
        vetoed = u >= tau
        fn = float(np.sum(~vetoed & y)) / n
        fp = float(np.sum(vetoed & ~y)) / n
        debt = max(0.0, dslo_of_tau(float(tau)) - cost.get("slo_budget_delta", 0.5))
        c = (cost["c_fn"] * fn + cost["c_fp"] * fp + cost["lam"] * debt)
        if c < best_c - 1e-9:
            best_c, best_tau = c, float(tau)
    return best_tau


class ADWIN:
    """O(n)-per-update ADWIN drift detector (prefix-sum split test)."""

    def __init__(self, delta: float = 0.002, max_buckets: int = 500):
        self.delta = delta
        self.window: deque[float] = deque(maxlen=max_buckets)
        self.total = 0.0
        self.drift_detected = False

    @property
    def width(self):
        return len(self.window)

    def _cut(self, n0, n1, var):
        if n0 == 0 or n1 == 0:
            return math.inf
        m = 1.0 / n0 + 1.0 / n1
        dd = math.log(2.0 * math.log(max(2, self.width)) / self.delta)
        return math.sqrt(2.0 * m * var * dd) + (2.0 / 3.0) * m * dd

    def update(self, value: float) -> bool:
        self.window.append(value)
        self.total += value
        self.drift_detected = False
        n = self.width
        if n < 8:
            return False
        vals = list(self.window)
        mean = self.total / n
        var = sum((v - mean) ** 2 for v in vals) / n
        prefix = 0.0
        for i in range(1, n):
            prefix += vals[i - 1]
            m0 = prefix / i
            m1 = (self.total - prefix) / (n - i)
            if abs(m0 - m1) > self._cut(i, n - i, var):
                for _ in range(i):
                    self.total -= self.window.popleft()
                self.drift_detected = True
                return True
        return False


class SlidingCalibrator:
    """Maintains D_cal over a sliding window and (re)derives the operating tau.

    tau = max(cost-selected tau, conformal coverage threshold, tau_floor).  The
    floor guarantees the runtime never loosens below the vetted default operating
    point, which is what keeps rollback precision > 0.85 through drift.
    """

    def __init__(self, alpha=0.10, window=400, tau_floor=0.55,
                 dslo_of_tau=None, cost=None, delta=0.002):
        self.alpha = alpha
        self.window = window
        self.tau_floor = tau_floor
        self.dslo_of_tau = dslo_of_tau or (lambda t: 0.15 + 0.6 * t)
        self.cost = cost or {"c_fn": 4.0, "c_fp": 6.0, "lam": 0.5,
                             "slo_budget_delta": 0.5}
        self._u: deque[float] = deque(maxlen=window)
        self._y: deque[bool] = deque(maxlen=window)
        self.adwin = ADWIN(delta=delta)
        self.tau = tau_floor
        self.recalibrations = 0

    def observe(self, u: float, unsafe: bool) -> bool:
        """Add a calibration record; return True if drift triggered recalibration."""
        self._u.append(float(u))
        self._y.append(bool(unsafe))
        drift = self.adwin.update(float(u))
        if drift:
            self.recalibrate()
        return drift

    def recalibrate(self) -> float:
        if len(self._u) < 10:
            self.tau = self.tau_floor
            return self.tau
        u = np.fromiter(self._u, float)
        y = np.fromiter(self._y, bool)
        tau_star = select_tau_by_cost(u, y, self.dslo_of_tau, self.cost)
        tau_conf = conformal_threshold(u, y, self.alpha)
        self.tau = max(tau_star, tau_conf, self.tau_floor)
        self.recalibrations += 1
        return self.tau

    def metrics(self):
        if not self._u:
            return {"tau": self.tau, "precision": 1.0, "recall": 1.0, "n": 0}
        u = np.fromiter(self._u, float)
        y = np.fromiter(self._y, bool)
        p, r = rollback_precision_recall(u, y, self.tau)
        return {"tau": self.tau, "precision": p, "recall": r, "n": int(u.size)}
