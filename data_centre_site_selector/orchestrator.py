from __future__ import annotations

import pandas as pd

from .agents import AgentRunner, run_critic, run_specialist_agents, run_synthesis
from .data_paths import CANDIDATE_FEATURES_CSV, LATEST_RANKINGS_CSV, LATEST_REPORT_MD, ensure_dirs
from .preprocess import build_candidate_features
from .report import build_markdown_report, terminal_report
from .scoring import score_for_workload


def load_or_build_features(rebuild: bool = False, include_flood: bool = False) -> tuple[pd.DataFrame, list[str]]:
    ensure_dirs()
    if CANDIDATE_FEATURES_CSV.exists() and not rebuild:
        return pd.read_csv(CANDIDATE_FEATURES_CSV), ["Loaded cached feature table."]
    features, diagnostics = build_candidate_features(include_flood=include_flood)
    features.to_csv(CANDIDATE_FEATURES_CSV, index=False)
    return features, diagnostics


def run_site_selection(
    query: str,
    workload: str,
    top_k: int = 5,
    rebuild_features: bool = False,
    include_flood: bool = False,
    model: str | None = None,
    use_agents: bool = True,
) -> dict:
    features, diagnostics = load_or_build_features(rebuild_features, include_flood)
    ranked = score_for_workload(features, workload)
    ensure_dirs()
    ranked.to_csv(LATEST_RANKINGS_CSV, index=False)
    runner = AgentRunner(model=model, enabled=use_agents) if model else AgentRunner(enabled=use_agents)
    agent_summaries = run_specialist_agents(runner, query, workload, ranked, top_k)
    critic = run_critic(runner, query, workload, ranked, agent_summaries)
    synthesis = run_synthesis(runner, query, workload, ranked, agent_summaries, critic)
    md = build_markdown_report(query, workload, ranked, agent_summaries, critic, synthesis, top_k)
    LATEST_REPORT_MD.write_text(md, encoding="utf-8")
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
