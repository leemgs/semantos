"""
controllers.py — Controller wrappers and a SemantOS control-loop object.

The four evaluation controllers (Baseline, Expert, BO/RL, SemantOS) are thin
wrappers over the calibrated response model.  `SemantOSLoop` implements
Algorithm 1 (telemetry -> KB retrieval -> reason -> conformal gate -> staged
rollout -> KB update / recalibrate) and is used by the 30-day drift study and
the Theorem-1 / Proposition-1 validations.
"""

from __future__ import annotations
import numpy as np

from . import spec, calibration as cal, conformal as cf
from .adwin import ADWIN
from .depgraph import DependencyGraph

CONTROLLERS = ["baseline", "expert", "bo_rl", "semantos"]
ABLATIONS = ["full", "wo_depgraph", "wo_rag", "wo_safety", "kb_only"]


class SemantOSLoop:
    """Online control loop with conformal-gated staged rollout and ADWIN drift.

    This drives the 30-day drift study: each step draws an action's uncertainty
    from the calibration mixture, the conformal gate + SLO guard decide
    accept/veto, and ADWIN + sliding-window recalibration keep coverage on target
    after drift events.
    """

    def __init__(self, alpha: float = spec.CONFORMAL_ALPHA,
                 window: int = 400, seed: int = spec.GLOBAL_SEED):
        self.alpha = alpha
        self.window = window
        self.rng = np.random.default_rng(seed)
        self.graph = DependencyGraph.induced(seed=0)
        self.adwin = ADWIN(delta=0.002)
        # bootstrap calibration; operate at the cost-selected default tau and
        # keep it valid via recalibration (Algorithm 1, lines 14-15).
        u0, y0 = cal.make_calibration_log(n=window, seed=seed)
        self._u = list(u0)
        self._y = list(y0)
        self.tau = self._cost_tau()
        self.recalibrations = 0

    def _cost_tau(self):
        u = np.array(self._u[-self.window:])
        y = np.array(self._y[-self.window:])
        tau_star, _ = cf.select_tau_by_cost(u, y, cal.dslo_of_tau, spec.COST)
        # coverage floor: never accept below the conformal coverage threshold,
        # and never loosen below the vetted default operating point.  Drift-time
        # recalibration may only *tighten* tau, which is what keeps rollback
        # precision > 0.85 through covariate shift (paper Sec. 6, drift study).
        tau_conf = cf.conformal_threshold(u, y, self.alpha)
        return max(tau_star, tau_conf, spec.DEFAULT_TAU)

    def recalibrate(self):
        self.tau = self._cost_tau()
        self.recalibrations += 1

    def step(self, u: float, unsafe: bool):
        """Process one recommendation. Returns (vetoed, slo_guard_fired)."""
        vetoed = u >= self.tau
        # independent SLO guard catches some residual unsafe during canary
        slo_fired = (not vetoed) and unsafe and (self.rng.random() < 0.7)
        rolled_back = vetoed or slo_fired
        self._u.append(u)
        self._y.append(unsafe)
        # feed drift detector; ADWIN drift -> immediate recalibration
        if self.adwin.update(u):
            self.recalibrate()
        return rolled_back, slo_fired

    def realized_metrics(self, n_recent: int | None = None):
        n = n_recent or self.window
        u = np.array(self._u[-n:])
        y = np.array(self._y[-n:])
        prec, rec = cf.rollback_precision_recall(u, y, self.tau)
        anomaly = cal.anomaly_from_precision(prec) / 100.0
        return {"tau": self.tau, "precision": prec, "recall": rec, "anomaly": anomaly}
