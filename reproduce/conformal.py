"""
conformal.py — Conformal-calibration-gated safety math (Theoretical Guarantees).

Implements, as runnable code:

  * split-conformal threshold tau such that  Pr[unsafe | u < tau] <= alpha
    (1 - alpha marginal coverage) from a calibration log D_cal of
    (uncertainty u, unsafe-label) tuples;
  * cost-based tau selection minimizing
        C(tau) = c_fn (1 - TPR(tau)) pi + c_fp FPR(tau) (1 - pi) + lam dSLO(tau)
    subject to dSLO(tau) <= delta  (Safety Runtime / UQ section);
  * sliding-window recalibration and the Proposition-1 coverage-recovery bound
        alpha' <= alpha + 1/(m+1) + eps ;
  * the Theorem-1 expected-cost decomposition (three levers alpha, beta_fp, dSLO).

The "unsafe" label is defined post hoc exactly as in the paper: an applied
action is unsafe iff it violated an SLO guard within its staged-rollout window
and triggered a rollback.  Here we consume that label directly.
"""

from __future__ import annotations
from dataclasses import dataclass

import numpy as np


@dataclass
class CalibrationResult:
    tau: float
    alpha: float
    coverage: float          # empirical Pr[safe | u < tau]
    beta_fp: float           # Pr[safe | u >= tau]  (over-veto probability)


def conformal_threshold(u: np.ndarray, unsafe: np.ndarray, alpha: float) -> float:
    """Split-conformal threshold on uncertainty scores.

    We want tau with Pr[unsafe | u < tau] <= alpha.  Using the unsafe examples'
    uncertainty distribution, tau is the (alpha)-lower quantile of unsafe
    scores: accepting below it leaves at most an alpha fraction of unsafe mass.
    """
    u = np.asarray(u, float)
    unsafe = np.asarray(unsafe, bool)
    u_bad = u[unsafe]
    if u_bad.size == 0:
        return 1.0
    # finite-sample conformal quantile (Jeary et al. 2024; Correia et al. 2024)
    n = u_bad.size
    q = np.clip(alpha * (n + 1) / n, 0.0, 1.0)
    return float(np.quantile(u_bad, q, method="higher"))


def evaluate_threshold(u: np.ndarray, unsafe: np.ndarray, tau: float) -> CalibrationResult:
    u = np.asarray(u, float)
    unsafe = np.asarray(unsafe, bool)
    accept = u < tau
    n_accept = max(1, accept.sum())
    n_veto = max(1, (~accept).sum())
    alpha_emp = float((unsafe & accept).sum() / n_accept)         # unsafe accepted
    coverage = 1.0 - alpha_emp
    beta_fp = float(((~unsafe) & (~accept)).sum() / n_veto)        # safe vetoed
    return CalibrationResult(tau=tau, alpha=alpha_emp, coverage=coverage, beta_fp=beta_fp)


def rollback_precision_recall(u: np.ndarray, unsafe: np.ndarray, tau: float):
    """Rollback = veto (u >= tau).  Precision/recall of catching unsafe actions."""
    u = np.asarray(u, float)
    unsafe = np.asarray(unsafe, bool)
    veto = u >= tau
    tp = int((veto & unsafe).sum())
    fp = int((veto & ~unsafe).sum())
    fn = int((~veto & unsafe).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall


def select_tau_by_cost(u, unsafe, dslo_of_tau, cost, grid=None):
    """Sweep tau on a grid and pick tau* minimizing C(tau) s.t. dSLO(tau)<=delta.

    dslo_of_tau: callable tau -> expected SLO deviation during canary/ramp.
    cost: dict with c_fn, c_fp, lam, slo_budget_delta.
    Returns (tau_star, table) where table maps tau -> dict of components.
    """
    u = np.asarray(u, float)
    unsafe = np.asarray(unsafe, bool)
    pi = float(unsafe.mean())
    if grid is None:
        grid = np.round(np.arange(0.20, 0.91, 0.05), 2)

    table = {}
    best_tau, best_c = None, np.inf
    for tau in grid:
        prec, rec = rollback_precision_recall(u, unsafe, tau)
        # TPR = recall of unsafe detection; FPR = safe actions vetoed / all safe
        veto = u >= tau
        safe = ~unsafe
        fpr = float((veto & safe).sum() / max(1, safe.sum()))
        tpr = rec
        dslo = float(dslo_of_tau(tau))
        c = (cost["c_fn"] * (1 - tpr) * pi
             + cost["c_fp"] * fpr * (1 - pi)
             + cost["lam"] * dslo)
        feasible = dslo <= cost["slo_budget_delta"]
        table[float(tau)] = {
            "precision": prec, "recall": rec, "tpr": tpr, "fpr": fpr,
            "dslo": dslo, "cost": c, "feasible": feasible,
        }
        if feasible and c < best_c:
            best_c, best_tau = c, float(tau)
    if best_tau is None:  # no feasible tau; fall back to global argmin
        best_tau = min(table, key=lambda k: table[k]["cost"])
    return best_tau, table


# --------------------------------------------------------------------------- #
# Proposition 1 — recalibration coverage recovery under drift.
# --------------------------------------------------------------------------- #

def proposition1_bound(alpha: float, m: int, eps: float) -> float:
    """alpha' <= alpha + 1/(m+1) + eps."""
    return alpha + 1.0 / (m + 1) + eps


def sliding_window_recalibrate(scores_stream, labels_stream, alpha, m):
    """Recalibrate tau on the most recent m samples; yields realized alpha' per step.

    Returns list of (step, tau, realized_alpha) after each new sample once the
    window has filled.
    """
    scores_stream = np.asarray(scores_stream, float)
    labels_stream = np.asarray(labels_stream, bool)
    out = []
    for i in range(m, len(scores_stream)):
        win_u = scores_stream[i - m:i]
        win_y = labels_stream[i - m:i]
        tau = conformal_threshold(win_u, win_y, alpha)
        res = evaluate_threshold(win_u, win_y, tau)
        out.append((i, tau, res.alpha))
    return out


# --------------------------------------------------------------------------- #
# Theorem 1 — expected per-decision cost decomposition (the three levers).
# --------------------------------------------------------------------------- #

def theorem1_expected_cost(pi, alpha, beta_fp, exp_dslo, cost):
    """E[C] <= c_fn*pi*alpha + c_fp*(1-pi)*beta_fp + lam*E[dSLO]."""
    safety = cost["c_fn"] * pi * alpha
    efficiency = cost["c_fp"] * (1 - pi) * beta_fp
    perf = cost["lam"] * exp_dslo
    return {
        "safety_risk": safety,
        "efficiency_loss": efficiency,
        "perf_degradation": perf,
        "bound": safety + efficiency + perf,
    }
