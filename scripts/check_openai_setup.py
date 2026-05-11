#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_centre_site_selector.config import DEFAULT_MODEL, load_environment


def mask_secret(value: str | None) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 10:
        return "<set but too short to mask safely>"
    return f"{value[:7]}...{value[-4:]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenAI SDK, .env loading, and a minimal model call.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), help="Model to test.")
    parser.add_argument("--timeout", type=float, default=30.0, help="OpenAI request timeout in seconds.")
    parser.add_argument("--skip-call", action="store_true", help="Only check local configuration; do not call OpenAI.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    print(f"[check] Repo root: {root}", flush=True)
    print(f"[check] .env exists: {env_path.exists()} ({env_path})", flush=True)

    load_environment()
    api_key = os.getenv("OPENAI_API_KEY")
    org = os.getenv("OPENAI_ORG_ID") or os.getenv("OPENAI_ORGANIZATION")
    project = os.getenv("OPENAI_PROJECT")

    print(f"[check] OPENAI_API_KEY: {mask_secret(api_key)}", flush=True)
    print(f"[check] OPENAI_MODEL/default model: {args.model}", flush=True)
    print(f"[check] OPENAI_ORG_ID/OPENAI_ORGANIZATION: {org or '<not set>'}", flush=True)
    print(f"[check] OPENAI_PROJECT: {project or '<not set>'}", flush=True)

    try:
        import openai
        from openai import OpenAI
    except Exception as exc:
        print(f"[check] OpenAI SDK import failed: {exc}", flush=True)
        return 1

    print(f"[check] openai package version: {getattr(openai, '__version__', '<unknown>')}", flush=True)

    if not api_key:
        print("[check] FAIL: OPENAI_API_KEY is missing. Add it to .env or export it in the shell.", flush=True)
        return 1
    if args.skip_call:
        print("[check] Local configuration looks usable. Skipped network call.", flush=True)
        return 0

    print(f"[check] Calling OpenAI with timeout={args.timeout}s.", flush=True)
    started = time.time()
    try:
        client = OpenAI(timeout=args.timeout)
        response = client.chat.completions.create(
            model=args.model,
            temperature=0,
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with exactly: openai setup ok"}],
        )
        elapsed = time.time() - started
        text = response.choices[0].message.content or ""
        print(f"[check] SUCCESS in {elapsed:.2f}s", flush=True)
        print(f"[check] Response: {text}", flush=True)
        return 0
    except Exception as exc:
        elapsed = time.time() - started
        print(f"[check] FAIL after {elapsed:.2f}s: {type(exc).__name__}: {exc}", flush=True)
        print("[check] If this is a timeout, try a longer timeout or check VPN/firewall/proxy/network access.", flush=True)
        print("[check] Example: python scripts/check_openai_setup.py --timeout 90", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
