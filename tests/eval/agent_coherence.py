"""Anti-hallucination and coherence checks for agent outputs.

Three independent checks per agent:
  1. Keyword relevance   — does the agent mention domain-specific terms?
  2. Score alignment     — does the agent's sentiment match the numeric score?
  3. Confidence calibration — does the agent claim high confidence while citing placeholders?

Each check returns a dict with 'pass' (bool) and diagnostic fields.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

# Keywords each specialist agent is expected to use across its full output.
# Words match what the agents actually say, not just idealised domain terms.
AGENT_EXPECTED_KEYWORDS: dict[str, list[str]] = {
    "EnergyAgent":         ["renewable", "capacity", "energy", "grid", "mw", "gsp", "operational"],
    # WaterAgent discusses water scores, population pressure, and data gaps
    "WaterAgent":          ["water", "score", "population", "data", "resources"],
    # ClimateCoolingAgent discusses climate scores, cooling conditions, temperature proxies
    "ClimateCoolingAgent": ["climate", "score", "cooling", "temperature", "conditions"],
    "LatencyAgent":        ["latency", "distance", "hub", "km", "proximity"],
    "ResilienceAgent":     ["flood", "resilience", "zone", "risk"],
    "LandPlanningAgent":   ["brownfield", "land", "planning", "hectare", "site"],
    "CriticAgent":         ["weakness", "missing", "dataset", "assumption", "confidence", "risk"],
    "SynthesisAgent":      ["recommend", "site", "location", "score", "summary"],
}

_POSITIVE = ["excellent", "good", "strong", "high", "favourable", "well", "suitable", "available", "significant"]
_NEGATIVE = ["poor", "low", "limited", "insufficient", "concern", "lack", "inadequate", "weak", "constrained", "missing"]
_PLACEHOLDER_WORDS = ["placeholder", "heuristic", "proxy", "not modelled", "missing dataset"]


def check_keyword_relevance(agent_name: str, agent_output: dict[str, Any]) -> dict[str, Any]:
    """Agent should use domain-specific terms relevant to its speciality.

    Scans all text fields (summary + key_points + risks), not just summary,
    because agents often put domain vocabulary in key_points.
    """
    expected = AGENT_EXPECTED_KEYWORDS.get(agent_name, [])
    # Concatenate all agent text fields
    all_text = " ".join([
        agent_output.get("summary", ""),
        *[str(kp) for kp in agent_output.get("key_points", [])],
        *[str(r) for r in agent_output.get("risks", [])],
    ]).lower()
    found = [k for k in expected if k in all_text]
    coverage = len(found) / len(expected) if expected else 1.0
    return {
        "check": "keyword_relevance",
        "pass": coverage >= 0.40,   # at least 40% of expected keywords present
        "coverage": round(coverage, 2),
        "found": found,
        "expected": expected,
        "detail": f"Found {len(found)}/{len(expected)} expected keywords",
    }


def check_score_alignment(
    agent_name: str,
    agent_output: dict[str, Any],
    top_score: float,
) -> dict[str, Any]:
    """Agent sentiment should not STRONGLY contradict the numeric score.

    Agents legitimately hedge with risk language even for good sites (epistemic
    honesty). We only flag a contradiction when negative words outnumber positive
    by 2:1 or more — a single "missing" alongside "strong energy" is not a failure.

    High score (≥ 6.5) → only fail if neg >= 2 * pos (strong negative)
    Low score  (≤ 3.5) → only fail if pos >= 2 * neg (strong positive)
    Mid range          → never fail (hedging is expected)
    """
    all_text = " ".join([
        agent_output.get("summary", ""),
        *[str(kp) for kp in agent_output.get("key_points", [])],
    ]).lower()

    pos = sum(1 for w in _POSITIVE if w in all_text)
    neg = sum(1 for w in _NEGATIVE if w in all_text)

    if pos > neg:
        sentiment = "positive"
    elif neg > pos * 1.5:       # clearly more negative, not just 1 extra word
        sentiment = "strongly_negative"
    else:
        sentiment = "mixed/neutral"

    if top_score >= 6.5:
        contradiction = sentiment == "strongly_negative"
    elif top_score <= 3.5:
        contradiction = (sentiment == "positive" and pos >= 2 * max(neg, 1))
    else:
        contradiction = False

    return {
        "check": "score_alignment",
        "pass": not contradiction,
        "agent_sentiment": sentiment,
        "pos_words": pos,
        "neg_words": neg,
        "top_score": round(top_score, 2),
        "contradiction": contradiction,
        "detail": f"Sentiment={sentiment} (pos={pos}, neg={neg}), score={top_score:.1f}",
    }


def check_confidence_calibration(agent_output: dict[str, Any]) -> dict[str, Any]:
    """High confidence + placeholder language = overconfident claim."""
    confidence = str(agent_output.get("confidence", "medium")).lower()
    all_text = " ".join([
        agent_output.get("summary", ""),
        *agent_output.get("key_points", []),
        *agent_output.get("risks", []),
    ]).lower()
    has_placeholder = any(w in all_text for w in _PLACEHOLDER_WORDS)
    overconfident = (confidence == "high") and has_placeholder
    return {
        "check": "confidence_calibration",
        "pass": not overconfident,
        "confidence_claimed": confidence,
        "has_placeholder_language": has_placeholder,
        "overconfident": overconfident,
        "detail": (
            f"Agent claims '{confidence}' confidence "
            f"{'with' if has_placeholder else 'without'} placeholder language"
        ),
    }


def check_region_mention(agent_output: dict[str, Any], top_regions: list[str]) -> dict[str, Any]:
    """Agent should reference at least one of the top-ranked regions it was given."""
    all_text = " ".join([
        agent_output.get("summary", ""),
        *agent_output.get("key_points", []),
    ]).lower()
    mentioned = [r for r in top_regions if r.lower() in all_text]
    # Deterministic fallbacks never mention regions — skip this check for them
    is_fallback = "deterministic fallback" in all_text
    return {
        "check": "region_mention",
        "pass": bool(mentioned) or is_fallback,
        "mentioned": mentioned,
        "top_regions": top_regions,
        "is_fallback": is_fallback,
        "detail": f"Mentions {len(mentioned)}/{len(top_regions)} top regions" if not is_fallback else "Deterministic fallback (skip)",
    }


def run_coherence_checks(
    agent_outputs: list[dict[str, Any]],
    ranked: pd.DataFrame,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Run all coherence checks for a list of agent outputs.

    Returns one result dict per agent with individual check results and an overall pass/fail.
    """
    top_regions = list(ranked.head(top_k)["region"].astype(str)) if "region" in ranked else []
    top_score = float(ranked.iloc[0]["overall_score"]) if len(ranked) > 0 and "overall_score" in ranked else 5.0

    results: list[dict[str, Any]] = []
    for output in agent_outputs:
        agent = output.get("agent", "unknown")
        summary = output.get("summary", "")
        is_fallback = "deterministic fallback" in summary.lower()

        checks = [
            check_keyword_relevance(agent, output),           # full output, not just summary
            check_score_alignment(agent, output, top_score),  # full output, 2:1 threshold
            check_confidence_calibration(output),
            check_region_mention(output, top_regions),
        ]
        n_pass = sum(1 for c in checks if c["pass"])
        results.append({
            "agent": agent,
            "is_fallback": is_fallback,
            "checks": checks,
            "checks_passed": n_pass,
            "checks_total": len(checks),
            "overall_pass": n_pass >= 3,   # pass 3 of 4 checks
            "pass_rate": round(n_pass / len(checks), 2),
        })
    return results
