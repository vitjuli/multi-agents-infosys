from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


RegionLevel = Literal["uk", "country", "city"]


@dataclass
class UserConstraints:
    prompt: str
    workload: str
    compute_mw: float | None = None
    region_text: str | None = None
    region_level: RegionLevel = "uk"
    budget_gbp: float | None = None
    optimisation_choices: list[str] = field(default_factory=list)
    policy_constraints: list[str] = field(default_factory=list)
    unspecified_fields: list[str] = field(default_factory=list)
    suggested_constraints: list[str] = field(default_factory=list)
    invalid_region: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SearchStage:
    level: RegionLevel
    label: str
    candidate_count: int
    criteria: list[str]
    top_regions: list[dict[str, Any]]
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetPlan:
    requested_compute_mw: float
    available_budget_gbp: float | None
    recommended_centre_count: int
    per_centre_compute_mw: float
    estimated_total_capex_gbp: float
    estimated_annual_opex_gbp: float
    budget_feasible: bool
    allocation: list[dict[str, Any]]
    cost_materials_summary: dict[str, Any]
    problem_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CentreRecommendation:
    location: str
    latitude: float
    longitude: float
    altitude_m: float
    priority_flag: str
    feasibility: bool
    text_summary: str
    problem_summary: str | None
    estimated_capex_gbp: float
    estimated_annual_opex_gbp: float
    compute_mw: float
    score_breakdown: dict[str, float]
    policy_points: list[str]
    grants_tax_breaks: list[str]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriticResult:
    name: str
    passed: bool
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SiteSelectionResult:
    constraints: UserConstraints
    feasibility: bool
    needs_human_input: bool
    human_input_prompt: str | None
    nested_search: list[SearchStage]
    recommendations: list[CentreRecommendation]
    budget_plan: BudgetPlan
    critic_results: list[CriticResult]
    explanation: str
    feedback_prompt: str
    policy_research: dict[str, Any] | None = None
    technical_report_path: str | None = None
    summary_report_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["constraints"] = self.constraints.to_dict()
        data["nested_search"] = [stage.to_dict() for stage in self.nested_search]
        data["recommendations"] = [rec.to_dict() for rec in self.recommendations]
        data["budget_plan"] = self.budget_plan.to_dict()
        data["critic_results"] = [critic.to_dict() for critic in self.critic_results]
        return data
