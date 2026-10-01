"""Class-conditional rank gate; empirical diagnostics, not deployment guarantees.

The score function must be fixed before calibration. Unsafe calibration examples
and the next unsafe example must be exchangeable. Selectively observed deployment
outcomes generally do not meet that assumption. Smaller tau accepts fewer actions.
"""
from __future__ import annotations
import math
from collections import deque
import numpy as np


def validate_records(u, y):
    u, y = np.asarray(u, dtype=float), np.asarray(y)
    if u.ndim != 1 or y.ndim != 1 or u.shape != y.shape:
        raise ValueError("scores and labels must be aligned one-dimensional arrays")
    if not np.all(np.isfinite(u)) or np.any((u < 0) | (u > 1)):
        raise ValueError("scores must be finite and in [0, 1]")
    if y.size and y.dtype.kind != 'b':
        raise ValueError("unsafe labels must be booleans, not strings or numbers")
    return u, y.astype(bool)


def conformal_threshold(u, y, alpha):
    """tau=unsafe order statistic floor(alpha*(n+1)); veto all if rank is zero.

    Under the assumptions above, P(U_new < tau | Y_new=unsafe) <= alpha,
    marginal over the calibration set and test example. This is NOT
    P(unsafe | accepted), nor a realized-window or drift recovery bound.
    Strict '<' acceptance is conservative under ties.
    """
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between zero and one")
    u, y = validate_records(u, y)
    bad = np.sort(u[y])
    rank = math.floor(alpha * (len(bad) + 1))
    return float(bad[rank - 1]) if rank else 0.0


def gate_counts(u, y, tau):
    u, y = validate_records(u, y)
    accept = u < tau
    return dict(tp=int(np.sum(~accept & y)), fp=int(np.sum(~accept & ~y)),
                fn=int(np.sum(accept & y)), tn=int(np.sum(accept & ~y)))


def ratio(n, d):
    return n / d if d else None


def rollback_precision_recall(u, y, tau):
    """Legacy function name: these are gate veto metrics, NOT rollback metrics."""
    c = gate_counts(u, y, tau)
    return ratio(c['tp'], c['tp'] + c['fp']), ratio(c['tp'], c['tp'] + c['fn'])


def select_tau_by_cost(u, y, dslo_of_tau, cost, grid=None):
    """Empirical optimization with a hard SLO constraint; infeasible => veto all."""
    u, y = validate_records(u, y)
    if not len(u):
        return 0.0
    if grid is None:
        grid = np.linspace(0, 1, 101)
    best_tau, best = 0.0, math.inf
    for tau in grid:
        if not math.isfinite(tau) or not 0 <= tau <= 1:
            raise ValueError("invalid threshold grid")
        debt = float(dslo_of_tau(float(tau)))
        if not math.isfinite(debt) or debt < 0 or debt > cost['slo_budget_delta']:
            continue
        c = gate_counts(u, y, tau)
        value = (cost['c_fn'] * c['fn'] + cost['c_fp'] * c['fp']) / len(u) + cost['lam'] * debt
        if value < best:
            best, best_tau = value, float(tau)
    return best_tau


class ADWIN:
    """Bounded-window split detector inspired by ADWIN; not a recovery theorem."""
    def __init__(self, delta=0.002, max_buckets=500):
        if not 0 < delta < 1 or max_buckets < 8:
            raise ValueError("invalid detector parameters")
        self.delta = delta
        self.window = deque(maxlen=max_buckets)
        self.total = 0.0
        self.drift_detected = False

    @property
    def width(self):
        return len(self.window)

    def update(self, value):
        if not math.isfinite(value):
            raise ValueError("nonfinite observation")
        if len(self.window) == self.window.maxlen:
            self.total -= self.window[0]
        self.window.append(value)
        self.total += value
        self.drift_detected = False
        n = self.width
        if n < 8:
            return False
        vals = np.asarray(self.window)
        var = float(np.var(vals))
        dd = math.log(2 * math.log(max(2, n)) / self.delta)
        prefix = 0.0
        for i in range(1, n):
            prefix += vals[i - 1]
            m = 1 / i + 1 / (n - i)
            cut = math.sqrt(2 * m * var * dd) + 2 / 3 * m * dd
            if abs(prefix / i - (self.total - prefix) / (n - i)) > cut:
                for _ in range(i):
                    self.total -= self.window.popleft()
                self.drift_detected = True
                break
        return self.drift_detected


class SlidingCalibrator:
    """Exploratory sliding calibration. tau_floor is a legacy name for a CAP.

    Cost tuning can only tighten the rank threshold. No score labels => veto all.
    Window refresh does not establish exchangeability or bound recovery time.
    """
    def __init__(self, alpha=0.1, window=400, tau_floor=0.55,
                 dslo_of_tau=None, cost=None, delta=0.002):
        if not 0 < alpha < 1 or window < 1 or not 0 <= tau_floor <= 1:
            raise ValueError("invalid calibration parameters")
        self.alpha, self.window, self.tau_cap = alpha, window, tau_floor
        self.dslo_of_tau, self.cost = dslo_of_tau, cost
        self._u, self._y = deque(maxlen=window), deque(maxlen=window)
        self.adwin = ADWIN(delta=delta)
        self.tau, self.recalibrations = 0.0, 0

    def observe(self, u, unsafe):
        validate_records([u], [unsafe])
        self._u.append(float(u)); self._y.append(unsafe)
        drift = self.adwin.update(float(u))
        if drift:
            # Old/new mixtures cannot justify a guarantee: hold until explicit refresh.
            self.tau = 0.0
        return drift

    def recalibrate(self):
        u, y = np.asarray(self._u), np.asarray(self._y, dtype=bool)
        tau = conformal_threshold(u, y, self.alpha)
        if self.dslo_of_tau is not None and self.cost is not None:
            tau = min(tau, select_tau_by_cost(u, y, self.dslo_of_tau, self.cost))
        self.tau = min(self.tau_cap, tau)
        self.recalibrations += 1
        return self.tau

    def metrics(self):
        u, y = np.asarray(self._u), np.asarray(self._y, dtype=bool)
        c = gate_counts(u, y, self.tau)
        p, r = rollback_precision_recall(u, y, self.tau)
        return dict(tau=self.tau, precision=p, recall=r, n=len(u), **c,
                    unsafe_given_accepted=ratio(c['fn'], c['fn'] + c['tn']),
                    acceptance_given_unsafe=ratio(c['fn'], c['fn'] + c['tp']),
                    veto_given_safe=ratio(c['fp'], c['fp'] + c['tn']),
                    scope='in_sample_diagnostic_not_a_guarantee')
