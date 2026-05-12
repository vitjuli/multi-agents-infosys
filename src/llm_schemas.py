from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserPreferencesPayload(BaseModel):
    audience: str = "technical"
    report_depth: str = "medium"
    preferred_style: str = "technical"
    primary_priorities: list[str] = Field(default_factory=list)
    risk_tolerance: str = "medium"
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)
    output_format: str = "decision-ready report"


class PreferenceUpdatePayload(BaseModel):
    audience: str | None = None
    report_depth: str | None = None
    preferred_style: str | None = None
    primary_priorities: list[str] | None = None
    risk_tolerance: str | None = None
    must_include: list[str] | None = None
    must_avoid: list[str] | None = None
    output_format: str | None = None


class ReportSectionPayload(BaseModel):
    name: str = "Section"
    purpose: str = ""
    depth: str = "medium"
    required_evidence: list[str] = Field(default_factory=list)


class AgentTaskPayload(BaseModel):
    agent: str = ""
    goal: str = ""
    required_outputs: list[str] = Field(default_factory=list)
    section_targets: list[str] = Field(default_factory=list)


class ReportBlueprintPayload(BaseModel):
    title: str = "UK Data Centre Site Feasibility Report"
    goal: str = ""
    sections: list[ReportSectionPayload] = Field(default_factory=list)
    agents_to_run: list[str] = Field(default_factory=list)
    agents_to_skip: list[str] = Field(default_factory=list)
    agent_tasks: list[AgentTaskPayload] = Field(default_factory=list)


class BlueprintCriticPayload(BaseModel):
    critic_score: float = 5.0
    passes_blueprint_check: bool = False
    missing_sections: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    clarity_score: float = 0.5
    risk_coverage_score: float = 0.5
    feedback: str = ""


class JsonObjectPayload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
