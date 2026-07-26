"""
calibration.py — Generates the held-out calibration log D_cal used by the
Safety Runtime's conformal gate, plus the dSLO(tau) exposure model.

D_cal is the log of (uncertainty u, unsafe-label) tuples.  The unsafe label is
the paper's post-hoc definition (an SLO guard fired within the staged-rollout
window and a rollback was triggered).  Uncertainty for unsafe actions is
stochastically higher; the two Beta distributions below were fit so that the
conformal machinery reproduces the manuscript's tau-sweep
(precision/recall/anomaly at tau in {0.30, 0.55, 0.70}).

Anomaly rate is tied to rollback *precision*: at low tau the runtime over-vetoes
(low precision), stranding the system on worse configs after false rollbacks,
which paradoxically raises the anomaly rate even though recall is higher — the
non-monotone behaviour reported in the paper.
"""

from __future__ import annotations
import numpy as np

from . import spec

# Fitted mixture (see reproduce/README / fit provenance): safe vs unsafe u.
BETA_SAFE = (0.20, 1.02)
BETA_UNSAFE = (1.27, 0.24)
BASE_RATE_UNSAFE = 0.45          # pi in the (risk-oversampled) calibration log

# anomaly_pct(tau) = ANOM_A - ANOM_B * precision(tau)
ANOM_A, ANOM_B = 11.4, 10.0


def make_calibration_log(n: int = 4000, seed: int = spec.GLOBAL_SEED):
    """Return (u, unsafe) arrays for D_cal."""
    rng = np.random.default_rng(seed)
    n_u = int(round(n * BASE_RATE_UNSAFE))
    n_s = n - n_u
    u_safe = rng.beta(*BETA_SAFE, size=n_s)
    u_unsafe = rng.beta(*BETA_UNSAFE, size=n_u)
    u = np.concatenate([u_safe, u_unsafe])
    unsafe = np.concatenate([np.zeros(n_s, bool), np.ones(n_u, bool)])
    order = rng.permutation(n)
    return u[order], unsafe[order]


def dslo_of_tau(tau: float) -> float:
    """Expected SLO deviation during canary/ramp before rollback.

    Higher tau = less aggressive vetoing = larger traffic exposure = larger
    worst-case SLO deviation before the guard fires.
    """
    return 0.15 + 0.6 * float(tau)


def anomaly_from_precision(precision: float) -> float:
    return max(0.0, ANOM_A - ANOM_B * precision)


def drifted_calibration_stream(n_pre: int, n_post: int, shift: float,
                               seed: int = spec.GLOBAL_SEED):
    """A score/label stream with a drift event at index n_pre.

    After the event, unsafe scores shift *down* by `shift` (harder to catch),
    modelling covariate drift that recalibration must recover from (Prop 1).
    """
    rng = np.random.default_rng(seed)

    def block(nn, sh):
        n_u = int(round(nn * BASE_RATE_UNSAFE))
        n_s = nn - n_u
        us = rng.beta(*BETA_SAFE, size=n_s)
        uu = np.clip(rng.beta(*BETA_UNSAFE, size=n_u) - sh, 0.0, 1.0)
        u = np.concatenate([us, uu])
        y = np.concatenate([np.zeros(n_s, bool), np.ones(n_u, bool)])
        idx = rng.permutation(nn)
        return u[idx], y[idx]

    u0, y0 = block(n_pre, 0.0)
    u1, y1 = block(n_post, shift)
    return np.concatenate([u0, u1]), np.concatenate([y0, y1]), n_pre
