"""Thin OpenAI chat wrapper used by all src/ modules."""
from __future__ import annotations

import json
import os
from pathlib import Path


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except ImportError:
        pass


def _client():
    _load_env()
    from openai import OpenAI
    return OpenAI()


def chat_json(system: str, user: str, model: str | None = None) -> dict:
    """Call OpenAI chat API and return parsed JSON dict. Falls back to empty dict on error."""
    _load_env()
    if model is None:
        model = os.getenv("OPENAI_MODEL_REASONING", os.getenv("OPENAI_MODEL", "gpt-4o"))
    try:
        client = _client()
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = response.choices[0].message.content or ""
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        return json.loads(text)
    except Exception as exc:
        return {"_error": str(exc)}


def chat_text(system: str, user: str, model: str | None = None) -> str:
    """Call OpenAI chat API and return plain text. Falls back to empty string on error."""
    _load_env()
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        client = _client()
        response = client.chat.completions.create(
            model=model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"[LLM unavailable: {exc}]"
