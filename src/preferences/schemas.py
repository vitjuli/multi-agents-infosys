"""Data classes for user preferences, report blueprints, and agent outputs."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class UserPreferences:
    audience: str = "technical"          # executive | technical | investor | general
    report_depth: str = "medium"         # short | medium | detailed
    preferred_style: str = "technical"   # executive | technical
    primary_priorities: list[str] = field(default_factory=list)
    risk_tolerance: str = "medium"       # low | medium | high
    must_include: list[str] = field(default_factory=list)
    must_avoid: list[str] = field(default_factory=list)
    output_format: str = "decision-ready report"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReportSection:
    name: str
    purpose: str
    depth: str                               # short | medium | detailed
    required_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTask:
    agent: str                               # existing agent name, e.g. "EnergyAgent"
    goal: str
    required_outputs: list[str] = field(default_factory=list)
    section_targets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReportBlueprint:
    title: str
    goal: str
    sections: list[ReportSection]
    agents_to_run: list[str]
    agents_to_skip: list[str]
    agent_tasks: list[AgentTask]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentOutput:
    agent_name: str
    section_targets: list[str]
    claims: list[dict[str, Any]]
    risks: list[str]
    uncertainties: list[str]
    data_gaps: list[str]
    recommendation_impact: str
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BlueprintCriticResult:
    critic_score: float
    passes_blueprint_check: bool
    missing_sections: list[str]
    missing_evidence: list[str]
    unsupported_claims: list[str]
    clarity_score: float
    risk_coverage_score: float
    feedback: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
