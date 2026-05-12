from __future__ import annotations

import os
from pathlib import Path

"""CAM'S COMMENTS:
config.py

   * candidate regions are hardcoded. Coordinates are extremely specific.
   * HUBS??? What are they?
   * Workload weights are hardcoded? What do they all even mean there is a category for each section but what does any of this mean?

"""


def load_environment() -> None:
    """Load repo-local .env values when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")


load_environment()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FAST_MODEL = os.getenv("OPENAI_MODEL_FAST", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
REASONING_MODEL = os.getenv(
    "OPENAI_MODEL_REASONING", os.getenv("OPENAI_MODEL", "gpt-4o")
)
WEB_MODEL = os.getenv("OPENAI_MODEL_WEB", REASONING_MODEL)
