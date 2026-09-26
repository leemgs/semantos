"""
figures.py — render the paper figures from the harness result CSVs.

Run *after* run_all.py has populated reproduce/results/.  Produces:
  * fig1_knob_synergy.png   — Figure 1  (knob-pair synergy on tail latency)
  * fig3_pareto.png         — Figure 3  (anomaly vs P95 Pareto frontier)
  * tau_sweep.png           — rollback precision/recall/anomaly vs tau
  * drift_study.png         — 30-day anomaly & rollback precision under drift

Usage:
    python -m reproduce.figures
"""
from __future__ import annotations

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import spec

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# muted, print-friendly palette
C_SEM = "#1b6ca8"
C_REF = "#a83279"
C_GREY = "#8a8f98"
C_OK = "#2a9d5c"


def _read(name):
    with open(os.path.join(RESULTS, name), newline="") as f:
        return list(csv.DictReader(f))


def _save(fig, name):
    path = os.path.join(RESULTS, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def fig1_knob_synergy():
    rows = _read("fig1.csv")
    labels = {
        "sched_min_granularity_ns_only": "min_granularity\nonly",
        "sched_wake_affinity_only": "wake_affinity\nonly",
        "combined": "combined\n(joint tuning)",
    }
    names = [labels.get(r["condition"], r["condition"]) for r in rows]
    vals = [float(r["latency_change%"]) for r in rows]
    cis = [float(r["ci%"]) for r in rows]
    colors = [C_GREY, C_GREY, C_SEM]

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    bars = ax.bar(names, vals, yerr=cis, capsize=5, color=colors,
                  edgecolor="black", linewidth=0.6, width=0.6)
    # sum-of-singles reference to visualize super-additivity
    singles_sum = vals[0] + vals[1]
    ax.axhline(singles_sum, color=C_REF, ls="--", lw=1.3,
               label=f"sum of singles ({singles_sum:.0f}%)")
    ax.set_ylabel("tail-latency change vs baseline (%)")
    ax.set_title("Figure 1 — knob-pair synergy (super-additive tail-latency gain)")
    ax.axhline(0, color="black", lw=0.8)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.0f}%", (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="top" if v < 0 else "bottom",
                    xytext=(0, -12 if v < 0 else 4), textcoords="offset points",
                    fontsize=10, fontweight="bold")
    ax.legend(loc="lower left", frameon=False)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, "fig1_knob_synergy.png")


def fig3_pareto():
    rows = _read("fig3.csv")
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    for r in rows:
        name = r["controller"]
        x = float(r["p95_latency_ms"])
        y = float(r["anomaly_rate%"])
        is_sem = name.lower().startswith("semantos")
        ax.scatter(x, y, s=140 if is_sem else 90,
                   color=C_SEM if is_sem else C_GREY,
                   edgecolor="black", zorder=3, marker="*" if is_sem else "o")
        ax.annotate(name, (x, y), xytext=(6, 6), textcoords="offset points",
                    fontsize=9, fontweight="bold" if is_sem else "normal")
    # connect the Pareto frontier (sorted by latency)
    pts = sorted(((float(r["p95_latency_ms"]), float(r["anomaly_rate%"]))
                  for r in rows), key=lambda p: p[0])
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=C_GREY,
            ls=":", lw=1.2, zorder=1)
    ax.set_xlabel("P95 latency (ms)  — lower is better")
    ax.set_ylabel("anomaly rate (%)  — lower is better")
    ax.set_title("Figure 3 — anomaly / latency Pareto frontier")
    ax.grid(alpha=0.25)
    ax.margins(0.15)
    return _save(fig, "fig3_pareto.png")


def tau_sweep_plot():
    rows = _read("tau_sweep.csv")
    taus = [float(r["tau"]) for r in rows]
    prec = [float(r["rollback_precision"]) for r in rows]
    rec = [float(r["rollback_recall"]) for r in rows]
    anom = [float(r["anomaly%"]) for r in rows]

    fig, ax1 = plt.subplots(figsize=(6.2, 4.2))
    ax1.plot(taus, prec, "-o", color=C_SEM, label="rollback precision")
    ax1.plot(taus, rec, "-s", color=C_REF, label="rollback recall")
    ax1.set_xlabel(r"veto threshold $\tau$")
    ax1.set_ylabel("precision / recall")
    ax1.set_ylim(0.7, 1.0)
    ax2 = ax1.twinx()
    ax2.plot(taus, anom, "-^", color=C_OK, label="anomaly rate (%)")
    ax2.set_ylabel("anomaly rate (%)", color=C_OK)
    ax2.tick_params(axis="y", labelcolor=C_OK)
    ax1.axvline(spec.DEFAULT_TAU, color=C_GREY, ls="--", lw=1.0)
    ax1.annotate(f"default $\\tau$={spec.DEFAULT_TAU}", (spec.DEFAULT_TAU, 0.72),
                 xytext=(4, 0), textcoords="offset points", fontsize=9)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="center right",
               frameon=False, fontsize=9)
    ax1.set_title(r"Safety runtime — precision/recall/anomaly vs $\tau$")
    ax1.grid(alpha=0.25)
    return _save(fig, "tau_sweep.png")


def drift_plot():
    rows = _read("drift_study.csv")
    days = [int(r["day"]) for r in rows]
    anom = [float(r["anomaly%"]) for r in rows]
    prec = [float(r["rollback_precision"]) for r in rows]
    drift_days = [int(r["day"]) for r in rows if r.get("drift_event") == "1"]

    fig, ax1 = plt.subplots(figsize=(7.0, 4.2))
    ax1.plot(days, anom, "-o", ms=4, color=C_REF, label="anomaly rate (%)")
    ax1.axhline(spec.PAPER_DRIFT["anomaly_ceiling"] * 100, color=C_REF, ls=":",
                lw=1.0, label="3% ceiling")
    ax1.set_xlabel("day")
    ax1.set_ylabel("anomaly rate (%)", color=C_REF)
    ax1.tick_params(axis="y", labelcolor=C_REF)
    ax1.set_ylim(0, 4)
    ax2 = ax1.twinx()
    ax2.plot(days, prec, "-s", ms=4, color=C_SEM, label="rollback precision")
    ax2.axhline(spec.PAPER_DRIFT["rollback_precision_floor"], color=C_SEM, ls=":",
                lw=1.0)
    ax2.set_ylabel("rollback precision", color=C_SEM)
    ax2.tick_params(axis="y", labelcolor=C_SEM)
    ax2.set_ylim(0.7, 1.0)
    for d in drift_days:
        ax1.axvspan(d - 0.4, d + 0.4, color=C_GREY, alpha=0.15)
    ax1.set_title("30-day drift study — recalibration holds anomaly < 3%, precision > 0.85")
    ax1.grid(alpha=0.2)
    return _save(fig, "drift_study.png")


def main():
    made = [fig1_knob_synergy(), fig3_pareto(), tau_sweep_plot(), drift_plot()]
    print("figures written:")
    for p in made:
        print("  " + p)


if __name__ == "__main__":
    main()
