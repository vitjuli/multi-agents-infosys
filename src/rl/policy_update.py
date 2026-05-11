"""Policy Update Module.

Implements a contextual-bandit-inspired weight update rule. After each run,
user feedback and critic scores are combined into a reward signal that nudges
the policy weights toward what worked and away from what didn't.

This is intentionally lightweight: no gradient descent, just normalised
additive adjustments guided by the reward and feedback keywords.
"""
from __future__ import annotations

from .blueprint_policy import load_policy, save_policy, _normalise
from ..preferences.schemas import BlueprintCriticResult, ReportBlueprint, UserPreferences
from ..rl.memory import save_run_to_memory


# Maps feedback keywords → which policy dimension to increase
_FEEDBACK_SIGNALS: list[tuple[list[str], str, float]] = [
    (["risk", "risky", "danger", "hazard", "concern"], "risk_severity", 0.12),
    (["uncertain", "uncertainty", "confident", "certain", "data gap"], "uncertainty_importance", 0.12),
    (["brief", "short", "concise", "simpler", "too long", "shorter"], "conciseness", 0.15),
    (["evidence", "proof", "support", "justify", "data", "source"], "evidence_strength", 0.12),
    (["decision", "recommend", "action", "clear", "direct"], "decision_relevance", 0.12),
]

# Inverse signals — user complaint about a dimension reduces it
_NEGATIVE_SIGNALS: list[tuple[list[str], str, float]] = [
    (["too detailed", "too long", "verbose", "too much methodology"], "evidence_strength", -0.08),
    (["not enough risk", "more risk"], "risk_severity", 0.15),
    (["too technical", "simpler", "less jargon"], "conciseness", 0.10),
]


def compute_reward(
    user_accepted: bool,
    critic_result: BlueprintCriticResult,
    blueprint_approved_first_try: bool,
    efficiency_score: float = 1.0,
) -> float:
    """Compute scalar reward [0, 1] for this run.

    reward = 0.40 * user_acceptance
           + 0.30 * critic_score
           + 0.20 * blueprint_approval
           + 0.10 * efficiency_score
    """
    return (
        0.40 * float(user_accepted)
        + 0.30 * (critic_result.critic_score / 10.0)
        + 0.20 * float(blueprint_approved_first_try)
        + 0.10 * min(max(efficiency_score, 0.0), 1.0)
    )


def update_policy_from_feedback(
    preferences: UserPreferences,
    blueprint: ReportBlueprint,
    critic_result: BlueprintCriticResult,
    user_feedback: str,
    blueprint_approved_first_try: bool = True,
    policy_path: str | None = None,
    memory_path: str | None = None,
) -> dict[str, float]:
    """Nudge policy weights based on feedback and critic result, then save.

    Returns the updated policy dict.
    """
    policy = load_policy(policy_path)
    feedback_lower = user_feedback.lower()

    # Detect whether user accepted or requested changes
    user_accepted = feedback_lower.strip() in (
        "yes", "accept", "accepted", "ok", "good", "approved", "looks good", "great", "perfect"
    )

    # Apply keyword-based adjustments
    for keywords, dimension, delta in _FEEDBACK_SIGNALS:
        if any(kw in feedback_lower for kw in keywords):
            policy[dimension] = policy.get(dimension, 0.0) + delta

    for keywords, dimension, delta in _NEGATIVE_SIGNALS:
        if any(kw in feedback_lower for kw in keywords):
            policy[dimension] = max(0.02, policy.get(dimension, 0.0) + delta)

    # Critic-driven adjustments
    if critic_result.missing_evidence:
        policy["evidence_strength"] = policy.get("evidence_strength", 0.0) + 0.08
    if critic_result.risk_coverage_score < 0.5:
        policy["risk_severity"] = policy.get("risk_severity", 0.0) + 0.08
    if critic_result.clarity_score < 0.5:
        policy["conciseness"] = policy.get("conciseness", 0.0) + 0.06

    # If user accepted, slightly reinforce current dominant weight
    if user_accepted:
        dominant = max(policy, key=policy.get)
        policy[dominant] = policy[dominant] * 1.05

    policy = _normalise(policy)

    reward = compute_reward(
        user_accepted=user_accepted,
        critic_result=critic_result,
        blueprint_approved_first_try=blueprint_approved_first_try,
    )

    save_policy(policy, policy_path)

    # Persist run summary to memory log
    run_data = {
        "preferences": preferences.to_dict(),
        "blueprint_goal": blueprint.goal,
        "critic_score": critic_result.critic_score,
        "reward": reward,
        "user_feedback": user_feedback[:200],
        "updated_policy": policy,
    }
    save_run_to_memory(run_data, memory_path)

    return policy
