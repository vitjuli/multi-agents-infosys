from __future__ import annotations

import pandas as pd

from .agents import AgentRunner, run_critic, run_specialist_agents, run_synthesis
from .data_paths import CANDIDATE_FEATURES_CSV, LATEST_RANKINGS_CSV, LATEST_REPORT_MD, ensure_dirs
from .preprocess import build_candidate_features
from .report import build_markdown_report, terminal_report
from .scoring import score_for_workload


def log(message: str) -> None:
    print(f"[run] {message}", flush=True)


def load_or_build_features(rebuild: bool = False, include_flood: bool = False) -> tuple[pd.DataFrame, list[str]]:
    ensure_dirs()
    if CANDIDATE_FEATURES_CSV.exists() and not rebuild:
        log(f"Loading cached features from {CANDIDATE_FEATURES_CSV}.")
        return pd.read_csv(CANDIDATE_FEATURES_CSV), ["Loaded cached feature table."]
    log("Building candidate feature table.")
    features, diagnostics = build_candidate_features(include_flood=include_flood)
    features.to_csv(CANDIDATE_FEATURES_CSV, index=False)
    log(f"Wrote feature cache to {CANDIDATE_FEATURES_CSV}.")
    return features, diagnostics


def run_site_selection(
    query: str,
    workload: str,
    top_k: int = 5,
    rebuild_features: bool = False,
    include_flood: bool = False,
    model: str | None = None,
    use_agents: bool = True,
    agent_timeout: float = 45.0,
) -> dict:
    log("Starting site-selection run.")
    features, diagnostics = load_or_build_features(rebuild_features, include_flood)
    log(f"Scoring {len(features)} candidate regions for workload '{workload}'.")
    ranked = score_for_workload(features, workload)
    ensure_dirs()
    ranked.to_csv(LATEST_RANKINGS_CSV, index=False)
    log(f"Wrote ranked results to {LATEST_RANKINGS_CSV}.")
    runner = AgentRunner(model=model, timeout=agent_timeout, enabled=use_agents) if model else AgentRunner(timeout=agent_timeout, enabled=use_agents)
    log("Running specialist agents.")
    agent_summaries = run_specialist_agents(runner, query, workload, ranked, top_k)
    log("Running critic agent.")
    critic = run_critic(runner, query, workload, ranked, agent_summaries)
    log("Running synthesis agent.")
    synthesis = run_synthesis(runner, query, workload, ranked, agent_summaries, critic)
    log("Building Markdown report.")
    md = build_markdown_report(query, workload, ranked, agent_summaries, critic, synthesis, top_k)
    LATEST_REPORT_MD.write_text(md, encoding="utf-8")
    log(f"Wrote Markdown report to {LATEST_REPORT_MD}.")
    log("Run complete.")
    return {
        "features": features,
        "ranked": ranked,
        "diagnostics": diagnostics,
        "agent_summaries": agent_summaries,
        "critic": critic,
        "synthesis": synthesis,
        "terminal": terminal_report(query, workload, ranked, agent_summaries, critic, synthesis, top_k),
        "report_path": LATEST_REPORT_MD,
        "rankings_path": LATEST_RANKINGS_CSV,
    }
