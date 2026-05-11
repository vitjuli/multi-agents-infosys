"""Score stability and determinism validation.

The numeric scoring pipeline must be fully deterministic:
same features + same constraints → identical scores every run.
This module verifies that invariant and reports any drift.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data_centre_site_selector.data_analysis import add_production_scores
from data_centre_site_selector.prompt_parser import parse_user_constraints
from data_centre_site_selector.scoring import add_raw_scores


_SCORE_COLS = [
    "overall_score",
    "energy_score_raw",
    "water_score_raw",
    "climate_score_raw",
    "latency_score_raw",
    "resilience_score_raw",
    "land_score_raw",
    "production_score",
]


def _available_cols(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c in df.columns]


def run_stability_check(
    features: pd.DataFrame,
    query: str = "Find 100 MW AI training location in Scotland",
    n_runs: int = 3,
) -> dict:
    """Run the deterministic scoring pipeline N times and check for score drift.

    Returns pass/fail, max deviation across all runs, and per-column stats.
    """
    constraints = parse_user_constraints(query)
    score_snapshots: list[pd.DataFrame] = []

    for _ in range(n_runs):
        scored = add_production_scores(features.copy(), constraints)
        cols = _available_cols(scored, _SCORE_COLS)
        snapshot = scored[["region"] + cols].copy().sort_values("region").reset_index(drop=True)
        score_snapshots.append(snapshot)

    # Compare run 0 against all subsequent runs
    deviations: dict[str, float] = {}
    mismatches: list[str] = []
    base = score_snapshots[0]

    for i, snap in enumerate(score_snapshots[1:], start=1):
        cols = _available_cols(base, _SCORE_COLS)
        for col in cols:
            if col not in snap.columns:
                continue
            diff = (base[col] - snap[col]).abs().max()
            key = f"run0_vs_run{i}_{col}"
            deviations[key] = round(float(diff), 6)
            if diff > 1e-9:
                mismatches.append(f"Run {i} col '{col}' drifted by {diff:.2e}")

    max_deviation = max(deviations.values()) if deviations else 0.0
    passed = max_deviation < 1e-9

    return {
        "check": "score_stability",
        "pass": passed,
        "n_runs": n_runs,
        "max_deviation": max_deviation,
        "mismatches": mismatches,
        "detail": (
            f"Scores identical across {n_runs} runs"
            if passed
            else f"Score drift detected: max deviation = {max_deviation:.2e}"
        ),
    }


def run_workload_ordering_check(features: pd.DataFrame) -> dict:
    """Verify workload weights produce expected score ordering.

    AI training should rank high-energy sites above low-energy ones.
    Financial latency should rank low-latency sites above high-latency ones.
    """
    from data_centre_site_selector.scoring import score_for_workload

    results: list[dict] = []

    # Check: ai_training top site has higher energy score than bottom site
    try:
        ai = score_for_workload(features.copy(), "ai_training")
        top_energy = float(ai.iloc[0]["energy_score_raw"])
        bot_energy = float(ai.iloc[-1]["energy_score_raw"])
        results.append({
            "check": "ai_training_energy_ordering",
            "pass": top_energy >= bot_energy,
            "top_energy": round(top_energy, 2),
            "bottom_energy": round(bot_energy, 2),
            "detail": f"Top site energy={top_energy:.2f}, bottom={bot_energy:.2f}",
        })
    except Exception as exc:
        results.append({"check": "ai_training_energy_ordering", "pass": False, "detail": str(exc)})

    # Check: financial_low_latency top site has lower hub distance than bottom site
    try:
        fin = score_for_workload(features.copy(), "financial_low_latency")
        if "nearest_major_hub_distance_km" in fin.columns:
            top_dist = float(fin.iloc[0]["nearest_major_hub_distance_km"])
            bot_dist = float(fin.iloc[-1]["nearest_major_hub_distance_km"])
            results.append({
                "check": "financial_latency_ordering",
                "pass": top_dist <= bot_dist,
                "top_hub_km": round(top_dist, 1),
                "bottom_hub_km": round(bot_dist, 1),
                "detail": f"Top site hub_dist={top_dist:.1f} km, bottom={bot_dist:.1f} km",
            })
    except Exception as exc:
        results.append({"check": "financial_latency_ordering", "pass": False, "detail": str(exc)})

    # Check: all scores in [0, 10]
    try:
        ai = score_for_workload(features.copy(), "ai_training")
        cols = _available_cols(ai, _SCORE_COLS)
        out_of_range = {}
        for col in cols:
            mn, mx = float(ai[col].min()), float(ai[col].max())
            if mn < -0.01 or mx > 10.01:
                out_of_range[col] = (round(mn, 3), round(mx, 3))
        results.append({
            "check": "score_range_validity",
            "pass": len(out_of_range) == 0,
            "out_of_range_cols": out_of_range,
            "detail": "All scores in [0, 10]" if not out_of_range else f"Range violations: {out_of_range}",
        })
    except Exception as exc:
        results.append({"check": "score_range_validity", "pass": False, "detail": str(exc)})

    return {
        "check": "workload_ordering",
        "sub_checks": results,
        "pass": all(r["pass"] for r in results),
        "passed": sum(1 for r in results if r["pass"]),
        "total": len(results),
    }
