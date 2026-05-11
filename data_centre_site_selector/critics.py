from __future__ import annotations

from .logging_utils import get_logger
from .schemas import BudgetPlan, CriticResult, UserConstraints


logger = get_logger("critics")


def run_deterministic_critics(constraints: UserConstraints, budget: BudgetPlan, recommendation_count: int) -> list[CriticResult]:
    results: list[CriticResult] = []
    scope_findings = []
    if constraints.invalid_region:
        scope_findings.append(f"Prompt mentioned non-UK region '{constraints.invalid_region}'; backend restricts recommendations to UK candidates.")
    if constraints.region_text == "Northern Ireland":
        scope_findings.append("No Northern Ireland candidate is present in the current cached candidate table.")
    results.append(CriticResult("ScopeCritic", not scope_findings, scope_findings or ["Region scope is UK-constrained and internally consistent."]))

    budget_findings = []
    if not budget.budget_feasible and budget.problem_summary:
        budget_findings.append(budget.problem_summary)
    if "budget_gbp" in constraints.unspecified_fields:
        budget_findings.append("Budget was unspecified; feasibility is based on cost estimates without a funding cap.")
    results.append(CriticResult("BudgetCritic", budget.budget_feasible, budget_findings or ["Budget allocation is internally consistent."]))

    data_findings = []
    if "compute_mw" in constraints.unspecified_fields:
        data_findings.append("Compute capacity was unspecified; defaulted to a 50 MW planning scenario.")
    if recommendation_count == 0:
        data_findings.append("No feasible centre recommendation could be generated for the selected scope.")
    data_findings.append("Water, climate, grid headroom, fibre latency, grants, and tax-site eligibility require stronger site-level datasets before investment decisions.")
    results.append(CriticResult("DataQualityCritic", recommendation_count > 0, data_findings))
    logger.debug("Deterministic critics complete: %s.", [(result.name, result.passed, result.findings) for result in results])
    return results


def critics_passed(results: list[CriticResult]) -> bool:
    return all(result.passed for result in results)
