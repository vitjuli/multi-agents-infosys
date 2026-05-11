"""Blueprint Policy Module.

Manages the policy weight vector that governs how the blueprint optimiser
prioritises sections, depth, and agent selection. Weights are persisted
to a JSON file so they update across sessions.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_POLICY: dict[str, float] = {
    "decision_relevance":    0.30,   # how much to prioritise decision-critical sections
    "risk_severity":         0.25,   # how prominently to feature risks
    "evidence_strength":     0.20,   # depth of evidence required per section
    "uncertainty_importance": 0.15,  # how much to surface data gaps / uncertainty
    "conciseness":           0.10,   # preference for shorter, sharper reports
}

_POLICY_PATH = Path(__file__).resolve().parents[3] / "data" / "policy" / "blueprint_policy.json"


def load_policy(path: str | Path | None = None) -> dict[str, float]:
    """Load policy from JSON file, returning defaults if file does not exist."""
    p = Path(path) if path else _POLICY_PATH
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # Merge with defaults so new keys are always present
            merged = {**DEFAULT_POLICY, **{k: float(v) for k, v in data.items() if k in DEFAULT_POLICY}}
            return _normalise(merged)
        except Exception:
            pass
    return dict(DEFAULT_POLICY)


def save_policy(policy: dict[str, float], path: str | Path | None = None) -> None:
    """Persist policy weights to JSON file."""
    p = Path(path) if path else _POLICY_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(policy, indent=2), encoding="utf-8")


def _normalise(policy: dict[str, float]) -> dict[str, float]:
    """Normalise weights to sum to 1.0."""
    total = sum(policy.values())
    if total <= 0:
        return dict(DEFAULT_POLICY)
    return {k: v / total for k, v in policy.items()}


def policy_summary(policy: dict[str, float]) -> str:
    """Return a one-line summary of the current policy weights."""
    return "  ".join(f"{k}={v:.2f}" for k, v in policy.items())
