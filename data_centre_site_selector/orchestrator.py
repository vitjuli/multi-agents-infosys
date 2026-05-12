from __future__ import annotations

import pandas as pd

from .agents import AgentRunner, run_critic, run_specialist_agents, run_synthesis
from .data_analysis import add_production_scores
from .data_paths import (
    CANDIDATE_FEATURES_CSV,
    LATEST_RANKINGS_CSV,
    LATEST_REPORT_MD,
    LATEST_SUMMARY_REPORT_MD,
    LATEST_PDF_REPORT,
    LATEST_PDF_PLOTS_DIR,
    ensure_dirs,
)
from .logging_utils import get_logger
from .planner import run_planner
from .preprocess import build_candidate_features
from .prompt_parser import parse_user_constraints
from .report import (
    build_markdown_report,
    production_markdown_report,
    production_terminal_report,
    terminal_report,
)

"""CAM'S COMMENTS:
orchestrator.py

    * **load\_or\_build\_features**

      * So is all our data going to be in pandas dataframes?
    * **run\_site\_selection**

      * parameters here?
    * idk what is going on...
"""
logger = get_logger("run")


def load_or_build_features(
    rebuild: bool = False, include_flood: bool = False
) -> tuple[pd.DataFrame, list[str]]:
    ensure_dirs()
    if CANDIDATE_FEATURES_CSV.exists() and not rebuild:
        logger.info("Loading cached features from %s.", CANDIDATE_FEATURES_CSV)
        cached = pd.read_csv(CANDIDATE_FEATURES_CSV)
        logger.debug(
            "Cached feature table shape=%s columns=%s",
            cached.shape,
            list(cached.columns),
        )
        if "candidate_source" in cached.columns and set(
            cached["candidate_source"].dropna()
        ) == {"ons_lad_boundary_centroid"}:
            return cached, ["Loaded cached dynamic feature table."]
        logger.info(
            "Cached feature table is not a dynamic national candidate table; rebuilding."
        )
    logger.info("Building candidate feature table.")
    features, diagnostics = build_candidate_features(include_flood=include_flood)
    features.to_csv(CANDIDATE_FEATURES_CSV, index=False)
    logger.info("Wrote feature cache to %s.", CANDIDATE_FEATURES_CSV)
    logger.debug(
        "Built feature table shape=%s diagnostics=%s", features.shape, diagnostics
    )
    return features, diagnostics


def run_site_selection(
    query: str,
    workload: str | None = None,
    top_k: int = 5,
    rebuild_features: bool = False,
    include_flood: bool = False,
    model: str | None = None,
    use_agents: bool = True,
    agent_timeout: float = 45.0,
    budget_gbp: float | None = None,
    region: str | None = None,
    target_location: str | None = None,
    target_radius_miles: float | None = None,
    compute_mw: float | None = None,
    optimisation_choices: list[str] | None = None,
    enable_web_policy: bool = False,
    generate_pdf: bool = True,
) -> dict:
    logger.info("Starting site-selection run.")
    logger.debug(
        "Run inputs query=%r workload=%r top_k=%s rebuild_features=%s include_flood=%s use_agents=%s web_policy=%s budget_gbp=%s region=%r target_location=%r target_radius_miles=%s compute_mw=%s optimise=%s",
        query,
        workload,
        top_k,
        rebuild_features,
        include_flood,
        use_agents,
        enable_web_policy,
        budget_gbp,
        region,
        target_location,
        target_radius_miles,
        compute_mw,
        optimisation_choices,
    )
    features, diagnostics = load_or_build_features(rebuild_features, include_flood)
    constraints = parse_user_constraints(
        prompt=query,
        workload=workload,
        budget_gbp=budget_gbp,
        region=region,
        target_location=target_location,
        target_radius_miles=target_radius_miles,
        compute_mw=compute_mw,
        optimisation_choices=optimisation_choices,
    )
    runner = (
        AgentRunner(
            model=model,
            timeout=agent_timeout,
            enabled=use_agents,
            enable_web=enable_web_policy,
        )
        if model
        else AgentRunner(
            timeout=agent_timeout, enabled=use_agents, enable_web=enable_web_policy
        )
    )
    constraints.workload_weights = runner.resolve_workload_weights(
        query=query,
        workload=constraints.workload,
        optimisation_choices=constraints.optimisation_choices,
    )
    logger.info(
        "Planning for workload '%s' across scope '%s'.",
        constraints.workload,
        constraints.region_text,
    )
    logger.debug("Parsed constraints: %s", constraints.to_dict())
    planning_result = run_planner(features, constraints, top_k)
    ranked = add_production_scores(features, constraints)
    ensure_dirs()
    ranked.to_csv(LATEST_RANKINGS_CSV, index=False)
    logger.info("Wrote ranked results to %s.", LATEST_RANKINGS_CSV)
    logger.debug(
        "Top ranked rows: %s",
        ranked[["region", "production_score", "overall_score"]]
        .head(top_k)
        .to_dict(orient="records"),
    )
    policy_research = None
    if enable_web_policy and (
        "political_favour" in constraints.optimisation_choices
        or constraints.policy_constraints
    ):
        logger.info("Running web-enabled policy research agent.")
        policy_research = runner.run_web_research(query, planning_result.to_dict())
        planning_result.policy_research = policy_research
    logger.info("Running specialist agents.")
    agent_summaries = run_specialist_agents(
        runner, query, constraints.workload, ranked, top_k
    )
    logger.info("Running critic agent.")
    critic = run_critic(runner, query, constraints.workload, ranked, agent_summaries)
    logger.info("Running synthesis agent.")
    synthesis = run_synthesis(
        runner, query, constraints.workload, ranked, agent_summaries, critic
    )
    logger.info("Building Markdown report.")
    md = build_markdown_report(
        query,
        constraints.workload,
        ranked,
        agent_summaries,
        critic,
        synthesis,
        top_k,
        constraints.workload_weights,
    )
    LATEST_REPORT_MD.write_text(md, encoding="utf-8")
    logger.info("Wrote Markdown report to %s.", LATEST_REPORT_MD)
    production_md = production_markdown_report(planning_result)
    LATEST_SUMMARY_REPORT_MD.write_text(production_md, encoding="utf-8")
    planning_result.technical_report_path = str(LATEST_REPORT_MD)
    planning_result.summary_report_path = str(LATEST_SUMMARY_REPORT_MD)
    logger.info("Wrote production summary report to %s.", LATEST_SUMMARY_REPORT_MD)

    # ── PDF report pipeline ─────────────────────────────────────────────
    pdf_report_path: str | None = None
    if generate_pdf:
        try:
            from .pdf_pipeline import run_pdf_report_pipeline
            logger.info("Generating PDF technical report via multi-agent pipeline.")
            LATEST_PDF_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
            pdf_report_path = run_pdf_report_pipeline(
                query=query,
                workload=constraints.workload,
                ranked=ranked,
                agent_summaries=agent_summaries,
                critic=critic,
                synthesis=synthesis,
                site_selection=planning_result.to_dict(),
                top_k=top_k,
                runner=runner,
                output_path=str(LATEST_PDF_REPORT),
                plot_dir=str(LATEST_PDF_PLOTS_DIR),
            )
            logger.info("PDF report written to %s.", pdf_report_path)
        except Exception as exc:
            logger.warning(
                "PDF report generation failed (non-fatal): %s", exc, exc_info=True
            )
    logger.debug(
        "Run result feasibility=%s needs_human_input=%s recommendations=%s budget_feasible=%s",
        planning_result.feasibility,
        planning_result.needs_human_input,
        [rec.location for rec in planning_result.recommendations],
        planning_result.budget_plan.budget_feasible,
    )
    logger.info("Run complete.")
    return {
        "features": features,
        "ranked": ranked,
        "diagnostics": diagnostics,
        "constraints": constraints.to_dict(),
        "site_selection": planning_result.to_dict(),
        "agent_summaries": agent_summaries,
        "policy_research": policy_research,
        "critic": critic,
        "synthesis": synthesis,
        "terminal": production_terminal_report(planning_result),
        "legacy_terminal": terminal_report(
            query,
            constraints.workload,
            ranked,
            agent_summaries,
            critic,
            synthesis,
            top_k,
        ),
        "report_path": LATEST_REPORT_MD,
        "summary_report_path": LATEST_SUMMARY_REPORT_MD,
        "rankings_path": LATEST_RANKINGS_CSV,
        "pdf_report_path": pdf_report_path,
    }
