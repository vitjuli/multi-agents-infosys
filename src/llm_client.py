"""Typed LangChain OpenAI wrappers used by src/ modules."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except ImportError:
        pass


def _chat_model(model: str | None = None):
    _load_env()
    from langchain_openai import ChatOpenAI

    selected_model = model or os.getenv(
        "OPENAI_MODEL_REASONING", os.getenv("OPENAI_MODEL", "gpt-4o")
    )
    return ChatOpenAI(model=selected_model, temperature=0.2)


def structured_chat(
    system: str,
    user: str,
    schema: type[T],
    model: str | None = None,
) -> T:
    llm = _chat_model(model)
    structured = llm.with_structured_output(schema)
    return structured.invoke(
        [
            ("system", system),
            ("human", user),
        ]
    )


def chat_json(
    system: str,
    user: str,
    model: str | None = None,
) -> dict:
    """Return a parsed JSON-like dict. Falls back to {'_error': ...} on failure."""
    _load_env()
    try:
        llm = _chat_model(model)
        response = llm.invoke(
            [
                ("system", system),
                ("human", user),
            ]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        return json.loads(text)
    except Exception as exc:
        return {"_error": str(exc)}


def chat_text(system: str, user: str, model: str | None = None) -> str:
    """Call OpenAI chat API and return plain text. Falls back to empty string."""
    _load_env()
    try:
        llm = _chat_model(model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        response = llm.invoke(
            [
                ("system", system),
                ("human", user),
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)
    except Exception as exc:
        return f"[LLM unavailable: {exc}]"
