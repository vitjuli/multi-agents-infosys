"""Preference Interview Module.

Collects user preferences through a brief interactive session. Infers
reasonable defaults from the query first, then asks only the questions
that remain ambiguous.
"""
from __future__ import annotations

import json

from .schemas import UserPreferences
from ..llm_client import chat_json


# ── keyword-based heuristics ────────────────────────────────────────────────

_AUDIENCE_SIGNALS = {
    "investor": ["investor", "investment", "fund", "capital", "return", "roi"],
    "executive": ["ceo", "board", "executive", "c-suite", "director", "strategy", "strategic"],
    "technical": ["engineer", "architect", "technical", "infrastructure", "latency", "mw", "megawatt", "compute"],
    "general": ["overview", "summary", "explain", "what is"],
}

_PRIORITY_SIGNALS = {
    "budget": ["cost", "budget", "price", "capex", "opex", "affordable", "cheap"],
    "low-carbon": ["co2", "carbon", "renewable", "green", "sustainable", "net zero"],
    "latency": ["latency", "speed", "fast", "low-latency", "financial", "hft"],
    "resilience": ["resilience", "flood", "risk", "disaster", "backup", "bdr"],
    "land": ["land", "brownfield", "planning", "site", "hectare"],
    "energy": ["energy", "power", "mw", "grid", "renewable", "capacity"],
    "policy": ["policy", "government", "grant", "tax", "incentive", "political"],
}


def _infer_from_query(query: str) -> UserPreferences:
    """Fast heuristic inference — no LLM call, instant."""
    q = query.lower()

    audience = "technical"
    for label, signals in _AUDIENCE_SIGNALS.items():
        if any(s in q for s in signals):
            audience = label
            break

    priorities: list[str] = []
    for label, signals in _PRIORITY_SIGNALS.items():
        if any(s in q for s in signals):
            priorities.append(label)
    if not priorities:
        priorities = ["energy", "low-carbon", "cost"]

    risk_tolerance = "low" if any(w in q for w in ["safe", "low risk", "conservative", "resilient"]) else "medium"

    depth = "detailed" if any(w in q for w in ["detail", "full", "comprehensive", "technical"]) else "medium"
    if any(w in q for w in ["brief", "short", "quick", "summary", "overview"]):
        depth = "short"

    style = "executive" if audience in ("executive", "investor") else "technical"

    return UserPreferences(
        audience=audience,
        report_depth=depth,
        preferred_style=style,
        primary_priorities=priorities[:4],
        risk_tolerance=risk_tolerance,
        must_include=["top recommendation", "top risks", "data uncertainty"],
        must_avoid=[],
        output_format="decision-ready report",
    )


def _llm_refine_preferences(query: str, base: UserPreferences) -> UserPreferences:
    """Use LLM to improve heuristic defaults. Returns base unchanged on failure."""
    system = (
        "You are a research assistant helping configure a UK data-centre site selection report. "
        "Analyse the user query and return a JSON object with these exact keys: "
        "audience (executive|technical|investor|general), "
        "report_depth (short|medium|detailed), "
        "preferred_style (executive|technical), "
        "primary_priorities (list of up to 4 from: budget, low-carbon, latency, resilience, land, energy, policy, uncertainty), "
        "risk_tolerance (low|medium|high), "
        "must_include (list of report elements), "
        "must_avoid (list of elements to omit), "
        "output_format (string). "
        "Be concise. Return ONLY the JSON object."
    )
    result = chat_json(system, f"Query: {query}\n\nCurrent defaults: {json.dumps(base.to_dict())}")
    if "_error" in result:
        return base

    def _get(key: str, default):
        val = result.get(key)
        return val if val is not None else default

    return UserPreferences(
        audience=_get("audience", base.audience),
        report_depth=_get("report_depth", base.report_depth),
        preferred_style=_get("preferred_style", base.preferred_style),
        primary_priorities=_get("primary_priorities", base.primary_priorities),
        risk_tolerance=_get("risk_tolerance", base.risk_tolerance),
        must_include=_get("must_include", base.must_include),
        must_avoid=_get("must_avoid", base.must_avoid),
        output_format=_get("output_format", base.output_format),
    )


def _ask(prompt: str, options: list[str], current: str) -> str:
    """Print a numbered menu and return the chosen value."""
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        marker = " (current)" if opt == current else ""
        print(f"    [{i}] {opt}{marker}")
    print(f"    [Enter] keep '{current}'")
    raw = input("  > ").strip()
    if not raw:
        return current
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        # treat as free text if it matches an option
        for opt in options:
            if raw.lower() in opt.lower():
                return opt
    return current


def collect_user_preferences(user_query: str, use_llm: bool = True) -> UserPreferences:
    """Run the preference interview. Returns a UserPreferences object.

    Heuristically infers defaults from the query, optionally refines them
    with an LLM call, then asks up to 3 targeted questions.
    """
    print("\n  Analysing your query to infer report preferences...", flush=True)
    prefs = _infer_from_query(user_query)

    if use_llm:
        prefs = _llm_refine_preferences(user_query, prefs)

    print("\n  Inferred defaults:")
    print(f"    Audience       : {prefs.audience}")
    print(f"    Depth          : {prefs.report_depth}")
    print(f"    Style          : {prefs.preferred_style}")
    print(f"    Priorities     : {', '.join(prefs.primary_priorities)}")
    print(f"    Risk tolerance : {prefs.risk_tolerance}")
    print(f"    Must include   : {', '.join(prefs.must_include)}")

    print("\n  Answer a few quick questions to refine (press Enter to keep default):")

    prefs.audience = _ask(
        "Who is the primary audience?",
        ["executive", "investor", "technical", "general"],
        prefs.audience,
    )
    prefs.preferred_style = "executive" if prefs.audience in ("executive", "investor") else prefs.preferred_style

    prefs.report_depth = _ask(
        "Report depth?",
        ["short", "medium", "detailed"],
        prefs.report_depth,
    )

    prefs.risk_tolerance = _ask(
        "Risk tolerance / how prominently should risks be shown?",
        ["low (show risks prominently)", "medium (balanced)", "high (de-emphasise risks)"],
        prefs.risk_tolerance,
    ).split(" ")[0]  # extract just the key word

    raw_include = input(
        f"\n  Additional must-include sections? (e.g. 'policy, methodology')\n"
        f"  [Enter to keep: {', '.join(prefs.must_include)}]\n  > "
    ).strip()
    if raw_include:
        extras = [s.strip() for s in raw_include.split(",") if s.strip()]
        prefs.must_include = list(dict.fromkeys(prefs.must_include + extras))

    raw_avoid = input(
        "\n  Anything to exclude? (e.g. 'methodology, raw data tables')\n"
        "  [Enter to skip]\n  > "
    ).strip()
    if raw_avoid:
        prefs.must_avoid = [s.strip() for s in raw_avoid.split(",") if s.strip()]

    return prefs


def update_preferences_from_feedback(preferences: UserPreferences, feedback: str) -> UserPreferences:
    """Parse natural-language feedback and return updated UserPreferences."""
    system = (
        "You adjust a UserPreferences object based on user feedback about a report blueprint. "
        "Return a JSON object with only the fields that should change. "
        "Valid keys: audience, report_depth, preferred_style, primary_priorities, "
        "risk_tolerance, must_include, must_avoid, output_format."
    )
    result = chat_json(
        system,
        f"Current preferences: {json.dumps(preferences.to_dict())}\n\nUser feedback: {feedback}",
    )
    if "_error" in result or not result:
        return preferences

    updated = UserPreferences(**preferences.to_dict())
    for key, value in result.items():
        if hasattr(updated, key) and value is not None:
            setattr(updated, key, value)
    return updated
