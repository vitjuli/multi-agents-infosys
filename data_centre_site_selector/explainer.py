from __future__ import annotations

from typing import Any

from .schemas import BudgetPlan, CentreRecommendation, CriticResult, UserConstraints


def priority_flag(score: float, feasible: bool) -> str:
    if not feasible:
        return "blocked"
    if score >= 8.0:
        return "high_priority"
    if score >= 6.5:
        return "priority"
    if score >= 5.0:
        return "watchlist"
    return "low_priority"


def centre_summary(region: str, score: float, scores: dict[str, float]) -> str:
    return (
        f"{region} scores {score:.2f}/10 on the production objective, with strongest support from "
        f"CO2={scores['co2']:.2f}, population strain={scores['population_strain']:.2f}, "
        f"policy={scores['political_favour']:.2f}, infrastructure={scores['infrastructure']:.2f}."
    )


def centre_explanation(region: str, scores: dict[str, float], policy_points: list[str], feasible: bool, problem: str | None) -> str:
    if not feasible:
        return f"{region} is not feasible under the current constraints: {problem}"
    policy_text = " ".join(policy_points[:2]) if policy_points else "No specific policy incentive was identified beyond national planning context."
    return (
        f"The planner ranked {region} by combining deterministic workload scoring with production criteria for carbon, "
        f"population water/energy strain, political favour, infrastructure, land reuse, resilience, latency, and cost. "
        f"The weighted profile favours candidates with high renewable capacity, lower community strain, practical grid/GSP access, "
        f"brownfield availability, and plausible UK policy support. {policy_text}"
    )


def build_overall_explanation(
    constraints: UserConstraints,
    budget: BudgetPlan,
    recommendations: list[CentreRecommendation],
    critic_results: list[CriticResult],
) -> str:
    if not recommendations:
        return "No centre recommendation could be produced for the selected UK scope. Review the region scope or add candidate data."
    top = recommendations[0]
    critic_text = "; ".join(f"{critic.name}: {'pass' if critic.passed else 'review'}" for critic in critic_results)
    return (
        f"Planner interpreted the request as workload={constraints.workload}, compute={budget.requested_compute_mw:.2f} MW, "
        f"scope={constraints.region_text}, budget={constraints.budget_gbp if constraints.budget_gbp is not None else 'unspecified'}. "
        f"It ran a nested UK-to-local search, asked the budget manager to allocate {budget.recommended_centre_count} centre(s), "
        f"and selected {top.location} as the leading option. Critics: {critic_text}."
    )


def feedback_prompt(constraints: UserConstraints) -> str:
    missing = ", ".join(constraints.unspecified_fields)
    if missing:
        return f"Please confirm or update these missing fields before final investment analysis: {missing}."
    return "Please confirm whether the weighting of CO2, community strain, political support, cost, latency, resilience, and land use matches your decision priorities."


def as_public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "feasibility": result["feasibility"],
        "needs_human_input": result["needs_human_input"],
        "human_input_prompt": result["human_input_prompt"],
        "recommendations": result["recommendations"],
        "budget_plan": result["budget_plan"],
        "explanation": result["explanation"],
        "feedback_prompt": result["feedback_prompt"],
    }
