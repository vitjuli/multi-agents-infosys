from __future__ import annotations

from typing import Any

import pandas as pd

from .logging_utils import get_logger
from .schemas import BudgetPlan, UserConstraints


logger = get_logger("budget")


DEFAULT_COMPUTE_MW = 50.0
MIN_VIABLE_CENTRE_MW = 10.0
TARGET_MAX_CENTRE_MW = 80.0
OPEX_PER_MW_GBP = 1_150_000.0
CONTINGENCY_RATE = 0.18


def recommended_centre_count(compute_mw: float, budget_gbp: float | None, capex_per_mw: float) -> int:
    technical_count = max(1, int((compute_mw + TARGET_MAX_CENTRE_MW - 1) // TARGET_MAX_CENTRE_MW))
    if budget_gbp is None:
        return technical_count
    affordable_compute = max(0.0, budget_gbp / (capex_per_mw * (1 + CONTINGENCY_RATE)))
    if affordable_compute < MIN_VIABLE_CENTRE_MW:
        return 1
    return min(technical_count, max(1, int(affordable_compute // MIN_VIABLE_CENTRE_MW)))


def build_materials_summary(total_compute_mw: float, total_capex_gbp: float) -> dict[str, Any]:
    return {
        "assumptions": [
            "Costs are class-5 planning estimates, not supplier quotes.",
            "Capex includes shell, MEP, grid interconnect, fit-out, security, design, and 18% contingency.",
            "Material quantities are first-order planning proxies for embodied-carbon and procurement discussion.",
        ],
        "estimated_total_capex_gbp": round(total_capex_gbp, 2),
        "estimated_steel_tonnes": round(total_compute_mw * 95, 1),
        "estimated_concrete_tonnes": round(total_compute_mw * 420, 1),
        "estimated_copper_tonnes": round(total_compute_mw * 12, 1),
        "estimated_cooling_plant_mw_thermal": round(total_compute_mw * 1.25, 1),
    }


def allocate_budget(scoped_candidates: pd.DataFrame, constraints: UserConstraints, top_k: int) -> BudgetPlan:
    requested_compute = constraints.compute_mw or DEFAULT_COMPUTE_MW
    budget = constraints.budget_gbp
    logger.debug(
        "Allocating budget scoped_candidates=%s requested_compute=%s budget=%s top_k=%s.",
        len(scoped_candidates),
        requested_compute,
        budget,
        top_k,
    )
    if scoped_candidates.empty:
        logger.warning("Budget allocation failed: no scoped candidates.")
        return BudgetPlan(
            requested_compute_mw=requested_compute,
            available_budget_gbp=budget,
            recommended_centre_count=0,
            per_centre_compute_mw=0,
            estimated_total_capex_gbp=0,
            estimated_annual_opex_gbp=0,
            budget_feasible=False,
            allocation=[],
            cost_materials_summary=build_materials_summary(0, 0),
            problem_summary="No candidate regions are available for the selected UK scope.",
        )

    candidates = scoped_candidates.head(max(1, top_k)).copy()
    median_capex = float(candidates["estimated_capex_per_mw_gbp"].median())
    centre_count = min(len(candidates), recommended_centre_count(requested_compute, budget, median_capex))
    centre_count = max(1, centre_count)
    per_centre_compute = requested_compute / centre_count
    allocations = []
    total_capex = 0.0
    total_opex = 0.0
    for _, row in candidates.head(centre_count).iterrows():
        capex = per_centre_compute * float(row["estimated_capex_per_mw_gbp"]) * (1 + CONTINGENCY_RATE)
        opex = per_centre_compute * OPEX_PER_MW_GBP
        total_capex += capex
        total_opex += opex
        allocations.append(
            {
                "region": row["region"],
                "compute_mw": round(per_centre_compute, 2),
                "estimated_capex_gbp": round(capex, 2),
                "estimated_annual_opex_gbp": round(opex, 2),
                "capex_per_mw_gbp": round(float(row["estimated_capex_per_mw_gbp"]), 2),
            }
        )
    feasible = budget is None or total_capex <= budget
    problem = None if feasible else f"Estimated capex GBP {total_capex:,.0f} exceeds stated budget GBP {budget:,.0f}."
    logger.debug(
        "Budget allocation complete centre_count=%s per_centre_compute=%s total_capex=%s total_opex=%s feasible=%s allocations=%s.",
        centre_count,
        per_centre_compute,
        total_capex,
        total_opex,
        feasible,
        allocations,
    )
    return BudgetPlan(
        requested_compute_mw=round(requested_compute, 2),
        available_budget_gbp=budget,
        recommended_centre_count=centre_count,
        per_centre_compute_mw=round(per_centre_compute, 2),
        estimated_total_capex_gbp=round(total_capex, 2),
        estimated_annual_opex_gbp=round(total_opex, 2),
        budget_feasible=feasible,
        allocation=allocations,
        cost_materials_summary=build_materials_summary(requested_compute, total_capex),
        problem_summary=problem,
    )
