"""Memory Module.

Persists a log of past blueprint runs. Each entry records preferences,
blueprint goal, critic score, reward, and feedback. This creates a history
that can be reviewed to understand how the policy evolved.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_MEMORY_PATH = Path(__file__).resolve().parents[3] / "data" / "policy" / "run_memory.json"


def save_run_to_memory(run_data: dict, path: str | Path | None = None) -> None:
    """Append a run summary to the memory log. Silently skips on any write error."""
    try:
        p = Path(path) if path else _MEMORY_PATH
        p.parent.mkdir(parents=True, exist_ok=True)

        history = load_memory(p)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **run_data,
        }
        history.append(entry)

        # Cap memory at last 50 runs
        if len(history) > 50:
            history = history[-50:]

        p.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def load_memory(path: str | Path | None = None) -> list[dict]:
    """Load the full run memory log. Returns an empty list if not found."""
    p = Path(path) if path else _MEMORY_PATH
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def memory_summary(path: str | Path | None = None) -> str:
    """Return a one-line summary of accumulated memory."""
    history = load_memory(path)
    if not history:
        return "No previous runs recorded."
    avg_reward = sum(r.get("reward", 0) for r in history) / len(history)
    last = history[-1]
    return (
        f"{len(history)} runs recorded | "
        f"avg reward: {avg_reward:.2f} | "
        f"last critic score: {last.get('critic_score', '?')}"
    )
