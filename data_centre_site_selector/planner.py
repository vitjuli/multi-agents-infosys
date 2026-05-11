from __future__ import annotations

import re
import pandas as pd

from .budget import allocate_budget
from .critics import run_deterministic_critics
from .data_analysis import nested_search
from .explainer import build_overall_explanation, centre_explanation, centre_summary, feedback_prompt, priority_flag
from .logging_utils import get_logger
from .policy import grant_tax_breaks, policy_points
from .schemas import CentreRecommendation, SiteSelectionResult, UserConstraints


logger = get_logger("planner")


def numeric_or_zero(value) -> float:
    return 0.0 if pd.isna(value) else float(value)


def build_recommendations(scoped: pd.DataFrame, constraints: UserConstraints, budget_plan) -> list[CentreRecommendation]:
    recommendations: list[CentreRecommendation] = []
    allocations = {item["region"]: item for item in budget_plan.allocation}
    logger.debug("Building recommendations scoped_count=%s allocation_regions=%s.", len(scoped), list(allocations))
    for _, row in scoped.head(max(1, budget_plan.recommended_centre_count)).iterrows():
        allocation = allocations.get(row["region"])
        if allocation is None:
            continue
        score = float(row["production_score"])
        feasible = budget_plan.budget_feasible and score >= 4.5
        problem = None
        if not budget_plan.budget_feasible:
            problem = budget_plan.problem_summary
        elif score < 4.5:
            problem = "Production score is below the minimum threshold for a recommended data-centre location."
        scores = {
            "production": round(score, 2),
            "base": round(float(row["overall_score"]), 2),
            "co2": round(float(row["co2_score_raw"]), 2),
            "population_strain": round(float(row["population_strain_score_raw"]), 2),
            "political_favour": round(float(row["political_favour_score_raw"]), 2),
            "cost": round(float(row["cost_score_raw"]), 2),
            "infrastructure": round(float(row["infrastructure_score_raw"]), 2),
            "land_use": round(float(row["land_use_score_raw"]), 2),
            "resilience": round(float(row["resilience_score_raw"]), 2),
            "latency": round(float(row["latency_score_raw"]), 2),
        }
        points = policy_points(row["region"], row.get("country"))
        recommendations.append(
            CentreRecommendation(
                location=row["region"],
                latitude=round(float(row["lat"]), 6),
                longitude=round(float(row["lon"]), 6),
                altitude_m=round(numeric_or_zero(row.get("alt_m")), 1),
                priority_flag=priority_flag(score, feasible),
                feasibility=feasible,
                text_summary=centre_summary(row["region"], score, scores),
                problem_summary=problem,
                estimated_capex_gbp=float(allocation["estimated_capex_gbp"]),
                estimated_annual_opex_gbp=float(allocation["estimated_annual_opex_gbp"]),
                compute_mw=float(allocation["compute_mw"]),
                score_breakdown=scores,
                policy_points=points,
                grants_tax_breaks=grant_tax_breaks(row["region"], row.get("country")),
                explanation=centre_explanation(row["region"], scores, points, feasible, problem),
            )
        )
        logger.debug("Recommendation built region=%s score=%s feasible=%s priority=%s.", row["region"], score, feasible, recommendations[-1].priority_flag)
    return recommendations


def infer_dynamic_region(features: pd.DataFrame, constraints: UserConstraints) -> None:
    if constraints.region_level != "uk":
        return
    prompt = constraints.prompt.lower()
    for region in sorted(features["region"].dropna().astype(str).unique(), key=len, reverse=True):
        if len(region) < 4:
            continue
        if re.search(rf"\b{re.escape(region.lower())}\b", prompt):
            constraints.region_level = "city"
            constraints.region_text = region
            logger.debug("Inferred local region from prompt: %s.", region)
            return


def run_planner(features: pd.DataFrame, constraints: UserConstraints, top_k: int = 5) -> SiteSelectionResult:
    logger.debug("Planner started features=%s constraints=%s top_k=%s.", len(features), constraints.to_dict(), top_k)
    if constraints.invalid_region:
        logger.warning("Non-UK region hint %r detected; resetting scope to UK-wide.", constraints.invalid_region)
        constraints.region_level = "uk"
        constraints.region_text = "UK-wide"
    infer_dynamic_region(features, constraints)
    scoped, stages = nested_search(features, constraints, top_k)
    budget_plan = allocate_budget(scoped, constraints, top_k)
    recommendations = build_recommendations(scoped, constraints, budget_plan)
    critic_results = run_deterministic_critics(constraints, budget_plan, len(recommendations))
    feasible = bool(recommendations) and budget_plan.budget_feasible and all(rec.feasibility for rec in recommendations)
    needs_human = bool(constraints.unspecified_fields) or any(not critic.passed for critic in critic_results)
    human_prompt = feedback_prompt(constraints) if needs_human else None
    explanation = build_overall_explanation(constraints, budget_plan, recommendations, critic_results)
    logger.debug(
        "Planner complete feasible=%s needs_human=%s recommendations=%s critics=%s.",
        feasible,
        needs_human,
        [rec.location for rec in recommendations],
        [(critic.name, critic.passed) for critic in critic_results],
    )
    return SiteSelectionResult(
        constraints=constraints,
        feasibility=feasible,
        needs_human_input=needs_human,
        human_input_prompt=human_prompt,
        nested_search=stages,
        recommendations=recommendations,
        budget_plan=budget_plan,
        critic_results=critic_results,
        explanation=explanation,
        feedback_prompt=feedback_prompt(constraints),
    )
