"""Blueprint Critic Module.

Evaluates the final report against the approved blueprint and user preferences.
Uses an LLM judge to assess coverage, clarity, risk visibility, and evidence.
Falls back to a rule-based evaluation when the LLM is unavailable.
"""
from __future__ import annotations

import json
import re

from ..preferences.schemas import BlueprintCriticResult, ReportBlueprint, UserPreferences
from ..llm_client import chat_json


def _rule_based_critic(
    final_report: str,
    blueprint: ReportBlueprint,
    preferences: UserPreferences,
) -> BlueprintCriticResult:
    """Fast rule-based critic used as fallback when LLM is unavailable."""
    report_lower = final_report.lower()

    missing_sections: list[str] = []
    for section in blueprint.sections:
        if section.name.lower() not in report_lower:
            missing_sections.append(section.name)

    missing_evidence: list[str] = []
    for section in blueprint.sections:
        for evidence in section.required_evidence:
            if evidence.lower() not in report_lower:
                missing_evidence.append(f"{section.name}: {evidence}")

    # Heuristic scores
    has_risks = any(w in report_lower for w in ["risk", "flood", "constraint", "gap", "missing"])
    has_uncertainty = "placeholder" in report_lower or "heuristic" in report_lower
    is_clear = len(final_report) > 500  # too short = not useful

    risk_coverage = 1.0 if has_risks else 0.3
    clarity = 0.8 if is_clear else 0.4
    coverage = 1.0 - (len(missing_sections) / max(len(blueprint.sections), 1))

    critic_score = round((coverage * 0.4 + risk_coverage * 0.3 + clarity * 0.3) * 10, 1)

    return BlueprintCriticResult(
        critic_score=critic_score,
        passes_blueprint_check=len(missing_sections) == 0,
        missing_sections=missing_sections,
        missing_evidence=missing_evidence[:5],
        unsupported_claims=[],
        clarity_score=round(clarity, 2),
        risk_coverage_score=round(risk_coverage, 2),
        feedback=(
            f"Rule-based check: {len(missing_sections)} missing sections, "
            f"{len(missing_evidence)} missing evidence items. "
            f"Score: {critic_score}/10."
        ),
    )


def critic_evaluate(
    final_report: str,
    blueprint: ReportBlueprint,
    preferences: UserPreferences,
) -> BlueprintCriticResult:
    """Evaluate the final report against the blueprint using an LLM judge.

    Falls back to rule-based evaluation if LLM is unavailable.
    """
    system = (
        "You are a critical report reviewer. Evaluate whether the provided report satisfies "
        "the approved blueprint and user preferences. Return a strict JSON object with keys: "
        "critic_score (float 0-10), "
        "passes_blueprint_check (bool), "
        "missing_sections (list of section names not covered), "
        "missing_evidence (list of evidence items not found), "
        "unsupported_claims (list of claims without data backing), "
        "clarity_score (float 0-1), "
        "risk_coverage_score (float 0-1), "
        "feedback (string with 1-3 sentences of constructive feedback). "
        "Be critical but fair. A score of 7+ means the report is usable."
    )

    context = {
        "blueprint": {
            "sections": [s.to_dict() for s in blueprint.sections],
            "agents_run": blueprint.agents_to_run,
        },
        "preferences": preferences.to_dict(),
        "report_excerpt": final_report[:3000],  # keep token cost bounded
        "instruction": (
            "Check: (1) Are all blueprint sections present? "
            "(2) Is required evidence cited per section? "
            "(3) Are risks and data gaps clearly shown? "
            "(4) Is the report appropriate for the stated audience? "
            "(5) Are there unsupported claims?"
        ),
    }

    result = chat_json(system, json.dumps(context))

    if "_error" in result or "critic_score" not in result:
        return _rule_based_critic(final_report, blueprint, preferences)

    try:
        return BlueprintCriticResult(
            critic_score=float(result.get("critic_score", 5.0)),
            passes_blueprint_check=bool(result.get("passes_blueprint_check", False)),
            missing_sections=result.get("missing_sections", []),
            missing_evidence=result.get("missing_evidence", []),
            unsupported_claims=result.get("unsupported_claims", []),
            clarity_score=float(result.get("clarity_score", 0.5)),
            risk_coverage_score=float(result.get("risk_coverage_score", 0.5)),
            feedback=result.get("feedback", ""),
        )
    except Exception:
        return _rule_based_critic(final_report, blueprint, preferences)


def print_critic_result(critic: BlueprintCriticResult) -> None:
    """Pretty-print critic result to stdout."""
    passed = "PASS" if critic.passes_blueprint_check else "NEEDS REVIEW"
    print(f"\n  Critic Score: {critic.critic_score:.1f}/10  [{passed}]")
    print(f"  Clarity:      {critic.clarity_score:.1%}")
    print(f"  Risk coverage:{critic.risk_coverage_score:.1%}")

    if critic.missing_sections:
        print(f"  Missing sections: {', '.join(critic.missing_sections)}")
    if critic.missing_evidence:
        print(f"  Missing evidence: {len(critic.missing_evidence)} items")
    if critic.unsupported_claims:
        print(f"  Unsupported claims: {len(critic.unsupported_claims)}")

    print(f"\n  Feedback: {critic.feedback}")
