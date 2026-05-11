"""Systematic Evaluation Runner.

Produces evidence for the criterion:
  "Can we see what fraction of the time each part of the system
   is doing what it's supposed to be doing?"

Four evaluation modules:
  1. Benchmark Suite       — 5 fixed queries, verifiable expected outputs (no-agents)
  2. Score Stability       — deterministic scoring identical across N runs
  3. Workload Ordering     — scoring weights produce expected rank ordering
  4. Ground Truth          — known UK DC clusters appear in top-N rankings
  5. Agent Coherence       — anti-hallucination checks (requires OPENAI_API_KEY)

Run:
    python tests/eval_runner.py                # deterministic checks only
    python tests/eval_runner.py --with-agents  # also run agent coherence (costs API tokens)
    python tests/eval_runner.py --fast         # skip stability repeat runs
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Repo root on path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from data_centre_site_selector.agents import AgentRunner, run_specialist_agents
from data_centre_site_selector.config import load_environment
from data_centre_site_selector.data_analysis import add_production_scores
from data_centre_site_selector.orchestrator import load_or_build_features
from data_centre_site_selector.planner import run_planner
from data_centre_site_selector.prompt_parser import parse_budget_gbp, parse_user_constraints

from data_centre_site_selector.data_paths import CANDIDATE_FEATURES_CSV

from tests.eval.benchmark_cases import BENCHMARK_CASES, BenchmarkCase
from tests.eval.ground_truth import check_known_sites_ranked, compute_precision_at_k
from tests.eval.agent_coherence import run_coherence_checks
from tests.eval.score_stability import run_stability_check, run_workload_ordering_check


# ── feature loading with graceful fallback ────────────────────────────────────

def _load_features_safe():
    """Try normal load, fall back to reading the CSV directly if geopandas missing."""
    import pandas as pd
    # 1. Try the normal pipeline (handles cache format checks + rebuild)
    try:
        features, _ = load_or_build_features()
        return features
    except RuntimeError as exc:
        if "geopandas" not in str(exc).lower():
            raise
        # geopandas not available in this env — try loading CSV directly
        pass

    # 2. Load the raw CSV directly — accept any size (note if small)
    if CANDIDATE_FEATURES_CSV.exists():
        try:
            df = pd.read_csv(CANDIDATE_FEATURES_CSV)
            if "region" in df.columns and len(df) >= 1:
                if len(df) < 50:
                    print(f"  [warn] Only {len(df)} candidates in cache (old format).")
                    print("         Full 370-region results available after feature rebuild.")
                    print("         Running eval on available data...\n")
                else:
                    print(f"  [warn] Loaded cached CSV directly ({len(df)} rows).")
                return df
        except Exception:
            pass

    return None


# ── helpers ──────────────────────────────────────────────────────────────────

def _tick(label: str) -> None:
    print(f"  {'.'*3} {label}", flush=True)


def _ok(label: str, passed: bool, detail: str = "") -> str:
    icon = "PASS" if passed else "FAIL"
    suffix = f"  — {detail}" if detail else ""
    return f"  [{icon}] {label}{suffix}"


def _section(title: str) -> None:
    print(f"\n{'─'*64}\n  {title}\n{'─'*64}")


# ── 1. benchmark suite ────────────────────────────────────────────────────────

def run_benchmark_case(
    case: BenchmarkCase,
    features,
    top_k: int = 5,
) -> dict:
    """Run one benchmark case and return pass/fail with diagnostics."""
    t0 = time.time()
    try:
        budget_gbp = parse_budget_gbp(case.budget) if case.budget else None
        constraints = parse_user_constraints(
            prompt=case.query,
            budget_gbp=budget_gbp,
            region=case.region,
            compute_mw=case.compute_mw,
        )
        planning = run_planner(features, constraints, top_k)
        ranked = add_production_scores(features, constraints)
    except Exception as exc:
        return {"case": case.name, "pass": False, "error": str(exc), "elapsed_s": time.time() - t0}

    elapsed = round(time.time() - t0, 2)
    checks: list[dict] = []

    # Check workload inference
    wl_ok = constraints.workload == case.expected_workload
    checks.append({
        "check": "workload_inferred",
        "pass": wl_ok,
        "expected": case.expected_workload,
        "got": constraints.workload,
    })

    # Check region scope
    scope_ok = constraints.region_level == case.expected_region_scope
    checks.append({
        "check": "region_scope",
        "pass": scope_ok,
        "expected": case.expected_region_scope,
        "got": constraints.region_level,
    })

    # Check minimum recommendations
    n_recs = len(planning.recommendations)
    recs_ok = n_recs >= case.min_recommendations
    checks.append({
        "check": "min_recommendations",
        "pass": recs_ok,
        "expected_min": case.min_recommendations,
        "got": n_recs,
    })

    # Check top recommendation country (if specified)
    if case.expected_top_country and planning.recommendations:
        top_loc = planning.recommendations[0].location
        top_row = ranked[ranked["region"] == top_loc]
        top_country = str(top_row.iloc[0]["country"]) if len(top_row) > 0 and "country" in top_row.columns else ""
        country_ok = case.expected_top_country.lower() in top_country.lower()
        checks.append({
            "check": "top_recommendation_country",
            "pass": country_ok,
            "expected": case.expected_top_country,
            "got": top_country,
            "top_location": top_loc,
        })

    # Check all scores are in [0, 10]
    score_cols = [c for c in ["overall_score", "production_score"] if c in ranked.columns]
    scores_valid = all(
        (0.0 <= float(ranked[c].min())) and (float(ranked[c].max()) <= 10.0)
        for c in score_cols
    )
    checks.append({
        "check": "score_range_valid",
        "pass": scores_valid,
        "cols_checked": score_cols,
    })

    n_pass = sum(1 for c in checks if c["pass"])
    return {
        "case": case.name,
        "pass": n_pass == len(checks),
        "checks_passed": n_pass,
        "checks_total": len(checks),
        "checks": checks,
        "elapsed_s": elapsed,
        "top_recommendation": planning.recommendations[0].location if planning.recommendations else None,
        "workload_inferred": constraints.workload,
    }


def run_benchmark_suite(features, top_k: int = 5) -> dict:
    _section("1. Benchmark Suite (5 canonical queries, no-agents mode)")
    results = []
    for case in BENCHMARK_CASES:
        _tick(case.name)
        r = run_benchmark_case(case, features, top_k)
        icon = "PASS" if r["pass"] else "FAIL"
        top = r.get("top_recommendation", "?")
        print(f"     [{icon}]  top={top}  elapsed={r.get('elapsed_s', '?')}s")
        results.append(r)

    n_pass = sum(1 for r in results if r["pass"])
    return {
        "module": "benchmark_suite",
        "pass": n_pass == len(results),
        "cases_passed": n_pass,
        "cases_total": len(results),
        "pass_rate": round(n_pass / len(results), 2),
        "results": results,
    }


# ── 2. score stability ────────────────────────────────────────────────────────

def run_stability_module(features, fast: bool = False) -> dict:
    _section("2. Score Stability (determinism across multiple runs)")
    n = 2 if fast else 3
    _tick(f"Running scoring pipeline {n} times, comparing results...")
    result = run_stability_check(features, n_runs=n)
    print(_ok("Identical scores across runs", result["pass"], result["detail"]))
    return {"module": "score_stability", **result}


# ── 3. workload ordering ──────────────────────────────────────────────────────

def run_ordering_module(features) -> dict:
    _section("3. Workload Ordering (weights produce expected rank order)")
    result = run_workload_ordering_check(features)
    for sub in result.get("sub_checks", []):
        print(_ok(sub["check"], sub["pass"], sub.get("detail", "")))
    return {"module": "workload_ordering", **result}


# ── 4. ground truth ───────────────────────────────────────────────────────────

def run_ground_truth_module(features) -> dict:
    _section("4. Ground Truth (known UK DC clusters in top rankings)")
    constraints = parse_user_constraints("Find the best UK data centre locations")
    ranked = add_production_scores(features, constraints)
    all_regions = list(ranked["region"].astype(str))

    prec = compute_precision_at_k(all_regions, k=20)
    coverage = check_known_sites_ranked(all_regions, top_n=50)

    print(_ok(f"Precision@20 (known DC LADs in top-20)", prec["pass"],
               f"{prec['hit_count']}/{prec['k']} hits = {prec['precision_at_k']:.0%}"))
    if prec["hits"]:
        print(f"     Hits: {', '.join(prec['hits'][:6])}")
    print(_ok(f"Cluster coverage in top-50", coverage["pass"],
               f"{len(coverage['clusters_found'])}/{coverage['total_clusters']} known clusters"))
    if coverage["clusters_missing"]:
        print(f"     Missing: {', '.join(coverage['clusters_missing'])}")

    return {
        "module": "ground_truth",
        "pass": prec["pass"] and coverage["pass"],
        "precision_at_20": prec,
        "cluster_coverage": coverage,
    }


# ── 5. agent coherence ────────────────────────────────────────────────────────

def run_agent_coherence_module(features) -> dict:
    _section("5. Agent Coherence (anti-hallucination checks)")

    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if not has_key:
        print("  [SKIP] OPENAI_API_KEY not set — skipping live agent checks.")
        print("         Re-run with API key to include agent coherence results.")
        return {
            "module": "agent_coherence",
            "pass": None,
            "skipped": True,
            "reason": "OPENAI_API_KEY not set",
        }

    constraints = parse_user_constraints(
        "Find 100 MW AI training locations in Scotland, optimise for low carbon"
    )
    ranked = add_production_scores(features, constraints)

    runner = AgentRunner(timeout=45.0, enabled=True)
    _tick("Running specialist agents against top-5 candidates...")
    t0 = time.time()
    agent_outputs = run_specialist_agents(runner, constraints.prompt, constraints.workload, ranked, top_k=5)
    elapsed = round(time.time() - t0, 1)
    _tick(f"Got {len(agent_outputs)} agent outputs in {elapsed}s")

    coherence_results = run_coherence_checks(agent_outputs, ranked, top_k=3)

    n_pass = sum(1 for r in coherence_results if r["overall_pass"])
    fallbacks = sum(1 for r in coherence_results if r["is_fallback"])

    for r in coherence_results:
        icon = "PASS" if r["overall_pass"] else "FAIL"
        fb = " [fallback]" if r["is_fallback"] else ""
        print(f"  [{icon}] {r['agent']}{fb}  "
              f"{r['checks_passed']}/{r['checks_total']} checks passed")
        for chk in r["checks"]:
            sub_icon = "ok" if chk["pass"] else "!!"
            print(f"         [{sub_icon}] {chk['check']}: {chk.get('detail', '')}")

    return {
        "module": "agent_coherence",
        "pass": n_pass >= len(coherence_results) * 0.6,   # 60% pass threshold
        "agents_passed": n_pass,
        "agents_total": len(coherence_results),
        "pass_rate": round(n_pass / len(coherence_results), 2) if coherence_results else 0.0,
        "fallback_count": fallbacks,
        "results": coherence_results,
        "elapsed_s": elapsed,
    }


# ── report writer ─────────────────────────────────────────────────────────────

def _status(passed) -> str:
    if passed is None:
        return "SKIPPED"
    return "PASS" if passed else "FAIL"


def write_evaluation_report(modules: list[dict], report_path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Systematic Evaluation Report",
        f"*Generated: {now}*\n",
        "## Summary\n",
        "| Module | Status | Pass Rate | Detail |",
        "|--------|--------|-----------|--------|",
    ]

    for m in modules:
        name = m.get("module", "unknown").replace("_", " ").title()
        status = _status(m.get("pass"))
        if "pass_rate" in m:
            rate = f"{m['pass_rate']:.0%}"
        elif "cases_passed" in m:
            rate = f"{m['cases_passed']}/{m['cases_total']}"
        elif "passed" in m:
            rate = f"{m['passed']}/{m.get('total', '?')}"
        else:
            rate = "—"
        detail = m.get("detail", m.get("reason", ""))
        lines.append(f"| {name} | **{status}** | {rate} | {detail} |")

    lines += ["", "---", ""]

    # Benchmark details
    bench = next((m for m in modules if m.get("module") == "benchmark_suite"), None)
    if bench:
        lines += ["## Benchmark Suite Details\n"]
        lines.append("| Query | Status | Top Recommendation | Workload Inferred | Time |")
        lines.append("|-------|--------|-------------------|-------------------|------|")
        for r in bench.get("results", []):
            st = "PASS" if r["pass"] else "FAIL"
            lines.append(
                f"| {r['case']} | **{st}** | {r.get('top_recommendation','?')} "
                f"| {r.get('workload_inferred','?')} | {r.get('elapsed_s','?')}s |"
            )
        lines += [
            "",
            f"**Overall benchmark pass rate: {bench['cases_passed']}/{bench['cases_total']} "
            f"({bench['pass_rate']:.0%})**\n",
        ]

    # Ground truth details
    gt = next((m for m in modules if m.get("module") == "ground_truth"), None)
    if gt:
        prec = gt.get("precision_at_20", {})
        cov = gt.get("cluster_coverage", {})
        lines += [
            "## Ground Truth Details\n",
            f"- **Precision@20**: {prec.get('precision_at_k', 0):.0%} "
            f"({prec.get('hit_count', 0)} of top-20 are known DC LADs)",
            f"- **Cluster coverage**: {len(cov.get('clusters_found', {}))}/{cov.get('total_clusters', 0)} "
            f"known clusters appear in top-50",
        ]
        if prec.get("hits"):
            lines.append(f"- Matched LADs: {', '.join(prec['hits'])}")
        lines.append("")

    # Stability details
    stab = next((m for m in modules if m.get("module") == "score_stability"), None)
    if stab:
        lines += [
            "## Score Stability Details\n",
            f"- Runs compared: {stab.get('n_runs', '?')}",
            f"- Max deviation: {stab.get('max_deviation', 0):.2e}",
            f"- Result: {stab.get('detail', '')}",
            "",
        ]

    # Ordering details
    order = next((m for m in modules if m.get("module") == "workload_ordering"), None)
    if order:
        lines += ["## Workload Ordering Details\n"]
        for sub in order.get("sub_checks", []):
            icon = "✓" if sub["pass"] else "✗"
            lines.append(f"- {icon} `{sub['check']}`: {sub.get('detail', '')}")
        lines.append("")

    # Agent coherence details
    coh = next((m for m in modules if m.get("module") == "agent_coherence"), None)
    if coh and not coh.get("skipped"):
        lines += [
            "## Agent Coherence Details\n",
            f"- Agents evaluated: {coh.get('agents_total', 0)}",
            f"- Agents passed all checks: {coh.get('agents_passed', 0)} "
            f"({coh.get('pass_rate', 0):.0%})",
            f"- Fallback agents: {coh.get('fallback_count', 0)} (skipped hallucination checks)",
            "",
        ]
        for r in coh.get("results", []):
            icon = "✓" if r["overall_pass"] else "✗"
            fb = " [fallback]" if r["is_fallback"] else ""
            lines.append(f"- {icon} **{r['agent']}{fb}**: {r['checks_passed']}/{r['checks_total']} checks")
        lines.append("")

    lines += [
        "---",
        "*Evaluation produced by `tests/eval_runner.py`.*",
        "*Deterministic modules require no API key. Agent coherence requires OPENAI_API_KEY.*",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Evaluation report saved to: {report_path}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Systematic evaluation runner.")
    parser.add_argument("--with-agents", action="store_true",
                        help="Run agent coherence checks (requires OPENAI_API_KEY).")
    parser.add_argument("--fast", action="store_true",
                        help="Fewer stability runs, skip slow checks.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--report", default="reports/evaluation_results.md",
                        help="Output path for the evaluation report.")
    args = parser.parse_args()

    load_environment()

    print("\n" + "━" * 64)
    print("  Systematic Evaluation — UK Data Centre Site Selector")
    print("━" * 64)

    # Load features once — reused across all modules
    print("\n  Loading feature table (cached if available)...", flush=True)
    t0 = time.time()
    features = _load_features_safe()
    if features is None:
        print("\n  [ERROR] Cannot load feature table.")
        print("  Run 'python scripts/build_features.py' first, or wait for an")
        print("  in-progress blueprint_main.py run to finish (it rebuilds the cache).")
        sys.exit(1)
    print(f"  Features ready: {len(features)} candidates in {time.time()-t0:.1f}s")

    modules: list[dict] = []

    modules.append(run_benchmark_suite(features, top_k=args.top_k))
    modules.append(run_stability_module(features, fast=args.fast))
    modules.append(run_ordering_module(features))
    modules.append(run_ground_truth_module(features))

    if args.with_agents or os.getenv("OPENAI_API_KEY"):
        modules.append(run_agent_coherence_module(features))
    else:
        modules.append({
            "module": "agent_coherence",
            "pass": None,
            "skipped": True,
            "reason": "Pass --with-agents or set OPENAI_API_KEY to enable",
        })

    # Overall summary
    _section("Overall Results")
    total_run = sum(1 for m in modules if m.get("pass") is not None)
    total_pass = sum(1 for m in modules if m.get("pass") is True)
    for m in modules:
        name = m.get("module", "?").replace("_", " ").title()
        st = _status(m.get("pass"))
        rate = f"{m['pass_rate']:.0%}" if "pass_rate" in m else ""
        print(f"  [{st}] {name}  {rate}")

    print(f"\n  Modules passed: {total_pass}/{total_run}")

    # Save JSON results
    json_path = _ROOT / "reports" / "evaluation_results.json"
    json_path.parent.mkdir(exist_ok=True)
    json_path.write_text(json.dumps(modules, indent=2, default=str), encoding="utf-8")

    # Write markdown report
    write_evaluation_report(modules, _ROOT / args.report)

    print("\n  Done.")


if __name__ == "__main__":
    main()
