from __future__ import annotations

import argparse
import contextlib
import json
import sys

from .blueprint_bridge import derive_optimisation_choices_from_blueprint
from .logging_utils import configure_logging, get_logger
from .orchestrator import run_site_selection
from .prompt_parser import parse_budget_gbp
from .workload_profiles import workload_profile_options
from src.planning.blueprint_startup import run_blueprint_startup

"""CAM'S COMMENTS:
data\_centre…/main.py

    * Hardcoded argument parsing? How do we interact with this? What do we need? What should be hardcoded or not? Are these just helpers?

"""

logger = get_logger("cli")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="UK production data-centre site-selection backend."
    )
    parser.add_argument(
        "--prompt",
        "--query",
        dest="query",
        default="Find the best UK location for a data centre",
        help="Natural-language decision prompt.",
    )
    parser.add_argument(
        "--workload",
        default=None,
        choices=sorted(workload_profile_options()),
        help="Workload profile. If omitted, inferred from the prompt.",
    )
    parser.add_argument(
        "--budget", default=None, help="Budget, for example '£1.2bn' or '500m GBP'."
    )
    parser.add_argument(
        "--region",
        default=None,
        help="UK scope: UK-wide, England, Scotland, Wales, Northern Ireland, or a supported city/cluster.",
    )
    parser.add_argument(
        "--target-location",
        default=None,
        help="Explicit target anchor, for example 'Manchester' or 'London'.",
    )
    parser.add_argument(
        "--target-radius-miles",
        type=float,
        default=None,
        help="Radius filter in miles around --target-location.",
    )
    parser.add_argument(
        "--compute-mw", type=float, default=None, help="Target IT compute/load in MW."
    )
    parser.add_argument(
        "--optimise",
        action="append",
        default=None,
        help="Optimisation priority. Can be repeated, e.g. --optimise co2 --optimise cost.",
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of ranked candidates to print."
    )
    parser.add_argument(
        "--rebuild-features", action="store_true", help="Rebuild cached feature table."
    )
    parser.add_argument(
        "--include-flood",
        action="store_true",
        help="Attempt to load the large EA flood-zone dataset during feature build.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model override. Defaults to OPENAI_MODEL or gpt-4o-mini.",
    )
    parser.add_argument(
        "--agent-timeout",
        type=float,
        default=45.0,
        help="OpenAI agent request timeout in seconds.",
    )
    parser.add_argument(
        "--no-agents",
        action="store_true",
        help="Skip OpenAI calls and use deterministic fallback agent messages.",
    )
    parser.add_argument(
        "--enable-web-policy",
        action="store_true",
        help="Allow the policy agent to use OpenAI web search for current UK policy/grant/tax context.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Ask once for clarification when required fields are missing or critics fail.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output instead of the terminal summary.",
    )
    parser.add_argument(
        "--debug-logs",
        "--debug",
        dest="debug",
        action="store_true",
        help="Enable verbose backend debug logging to stderr.",
    )
    parser.add_argument(
        "--log-file", default=None, help="Write full debug logs to this file."
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF technical report generation.",
    )
    parser.add_argument(
        "--blueprint-mode",
        action="store_true",
        help=(
            "Use blueprint startup to infer initial run conditions before the standard site-selection run. "
            "This is the default unless --skip-blueprint-startup is set."
        ),
    )
    parser.add_argument(
        "--skip-blueprint-startup",
        action="store_true",
        help="Run the legacy direct site-selection startup without blueprint preference/structure generation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(debug=args.debug, log_file=args.log_file)
    logger.debug("CLI args parsed: %s", vars(args))

    query = args.query
    optimisation_choices = args.optimise
    if not args.skip_blueprint_startup:
        stream = sys.stderr if args.json else sys.stdout
        with contextlib.redirect_stdout(stream):
            startup = run_blueprint_startup(
                query,
                use_llm_preferences=not args.no_agents,
                interactive=args.interactive,
            )
        query = startup.user_query
        if optimisation_choices is None:
            optimisation_choices = derive_optimisation_choices_from_blueprint(startup) or None
            logger.debug(
                "Blueprint-derived optimisation choices: %s",
                optimisation_choices,
            )

    budget_gbp = parse_budget_gbp(args.budget) if args.budget else None
    logger.debug("Parsed budget_gbp=%s from budget=%r", budget_gbp, args.budget)
    result = run_site_selection(
        query=query,
        workload=args.workload,
        top_k=args.top_k,
        rebuild_features=args.rebuild_features,
        include_flood=args.include_flood,
        model=args.model,
        use_agents=not args.no_agents,
        agent_timeout=args.agent_timeout,
        budget_gbp=budget_gbp,
        region=args.region,
        target_location=args.target_location,
        target_radius_miles=args.target_radius_miles,
        compute_mw=args.compute_mw,
        optimisation_choices=optimisation_choices,
        enable_web_policy=args.enable_web_policy,
        generate_pdf=not args.no_pdf,
    )
    if args.interactive and result["site_selection"]["needs_human_input"]:
        logger.info("Interactive clarification requested by planner.")
        answer = input(
            f"{result['site_selection']['human_input_prompt']}\nAdditional input: "
        ).strip()
        if answer:
            logger.debug(
                "Received interactive clarification with %d characters.", len(answer)
            )
            result = run_site_selection(
                query=f"{query}\nAdditional user input: {answer}",
                workload=args.workload,
                top_k=args.top_k,
                rebuild_features=args.rebuild_features,
                include_flood=args.include_flood,
                model=args.model,
                use_agents=not args.no_agents,
                agent_timeout=args.agent_timeout,
                budget_gbp=budget_gbp,
                region=args.region,
                target_location=args.target_location,
                target_radius_miles=args.target_radius_miles,
                compute_mw=args.compute_mw,
                optimisation_choices=optimisation_choices,
                enable_web_policy=args.enable_web_policy,
                generate_pdf=not args.no_pdf,
            )
    if args.json:
        logger.debug("Printing structured JSON result.")
        print(json.dumps(result["site_selection"], indent=2, default=str))
    else:
        logger.debug("Printing terminal report.")
        print(result["terminal"])
    status_stream = sys.stderr if args.json else sys.stdout
    print(f"Saved ranked results to {result['rankings_path']}", file=status_stream)
    print(f"Saved Markdown report to {result['report_path']}", file=status_stream)
    print(
        f"Saved production summary to {result['summary_report_path']}",
        file=status_stream,
    )
    if result.get("pdf_report_path"):
        print(
            f"Saved PDF technical report to {result['pdf_report_path']}",
            file=status_stream,
        )
    elif not args.no_pdf:
        print(
            "PDF report generation was skipped or failed (see logs).",
            file=status_stream,
        )


if __name__ == "__main__":
    main()
