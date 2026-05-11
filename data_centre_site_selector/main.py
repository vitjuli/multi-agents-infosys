from __future__ import annotations

import argparse

from .config import WORKLOAD_WEIGHTS
from .orchestrator import run_site_selection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UK data-centre site-selection baseline.")
    parser.add_argument("--query", default="Find the best UK location for a data centre", help="Natural-language decision query.")
    parser.add_argument("--workload", default="ai_training", choices=sorted(WORKLOAD_WEIGHTS), help="Workload profile.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of ranked candidates to print.")
    parser.add_argument("--rebuild-features", action="store_true", help="Rebuild cached feature table.")
    parser.add_argument("--include-flood", action="store_true", help="Attempt to load the large EA flood-zone dataset during feature build.")
    parser.add_argument("--model", default=None, help="OpenAI model override. Defaults to OPENAI_MODEL or gpt-4o-mini.")
    parser.add_argument("--no-agents", action="store_true", help="Skip OpenAI calls and use deterministic fallback agent messages.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_site_selection(
        query=args.query,
        workload=args.workload,
        top_k=args.top_k,
        rebuild_features=args.rebuild_features,
        include_flood=args.include_flood,
        model=args.model,
        use_agents=not args.no_agents,
    )
    print(result["terminal"])
    print(f"Saved ranked results to {result['rankings_path']}")
    print(f"Saved Markdown report to {result['report_path']}")


if __name__ == "__main__":
    main()
