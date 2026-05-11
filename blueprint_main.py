"""Preference-Guided Research Blueprint — demo entry point.

Architecture:
  User query
  → Preference Interview          (src/preferences/interview.py)
  → Report Blueprint Optimiser    (src/planning/blueprint_optimizer.py)
  → Human Approval Gate           (loop until approved)
  → Feature loading + scoring     (existing data_centre_site_selector pipeline)
  → Blueprint-guided Agent Dispatch (src/planning/task_dispatcher.py)
  → Final Report Composer         (src/reports/final_report_composer.py)
  → Blueprint Critic              (src/reports/critic.py)
  → Policy Update                 (src/rl/policy_update.py)

Run:
    python blueprint_main.py
    python blueprint_main.py --prompt "100MW AI training in Scotland, low carbon"
    python blueprint_main.py --no-agents  # skip OpenAI agent calls
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is on path for both package imports
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

# ── existing pipeline imports ────────────────────────────────────────────────
from data_centre_site_selector.agents import AgentRunner
from data_centre_site_selector.config import load_environment
from data_centre_site_selector.data_analysis import add_production_scores
from data_centre_site_selector.logging_utils import configure_logging
from data_centre_site_selector.orchestrator import load_or_build_features
from data_centre_site_selector.planner import run_planner
from data_centre_site_selector.prompt_parser import parse_budget_gbp, parse_user_constraints

# ── new blueprint system imports ─────────────────────────────────────────────
from src.preferences.interview import collect_user_preferences, update_preferences_from_feedback
from src.planning.blueprint_optimizer import optimise_report_blueprint
from src.planning.report_blueprint import blueprint_to_text, print_blueprint
from src.planning.task_dispatcher import run_agents_from_blueprint
from src.rl.blueprint_policy import load_policy, policy_summary
from src.rl.memory import memory_summary
from src.rl.policy_update import update_policy_from_feedback
from src.reports.critic import critic_evaluate, print_critic_result
from src.reports.final_report_composer import compose_final_report

_REPORT_DIR = _ROOT / "reports"
_REPORT_DIR.mkdir(exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def _banner(text: str, width: int = 64) -> None:
    print(f"\n{'━' * width}")
    print(f"  {text}")
    print(f"{'━' * width}")


def _print_policy(policy: dict) -> None:
    print(f"\n  Active policy weights: {policy_summary(policy)}")


def _save_report(content: str, filename: str = "blueprint_report.md") -> Path:
    path = _REPORT_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


# ── argument parsing ─────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preference-Guided Blueprint Demo for UK Data Centre Site Selection."
    )
    parser.add_argument("--prompt", default=None, help="Initial research query (skips input prompt).")
    parser.add_argument("--budget", default=None, help="Budget, e.g. '£1.2bn'.")
    parser.add_argument("--region", default=None, help="UK region scope.")
    parser.add_argument("--compute-mw", type=float, default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-agents", action="store_true", help="Skip OpenAI agent calls.")
    parser.add_argument("--no-llm-prefs", action="store_true", help="Skip LLM preference refinement.")
    parser.add_argument("--model", default=None)
    parser.add_argument("--agent-timeout", type=float, default=45.0)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--json", dest="json_out", action="store_true", help="Also dump JSON output.")
    return parser.parse_args()


# ── main flow ────────────────────────────────────────────────────────────────

def main() -> None:
    args = _parse_args()
    configure_logging(debug=args.debug)
    load_environment()

    # ── 0. Greet ──────────────────────────────────────────────────────────────
    _banner("Preference-Guided Research Blueprint System")
    print("  UK AI Data Centre Site Selection | Hackathon Demo")
    mem = memory_summary()
    print(f"  Memory: {mem}")

    # ── 1. User query ─────────────────────────────────────────────────────────
    if args.prompt:
        user_query = args.prompt
        print(f"\n  Query: {user_query}")
    else:
        print()
        user_query = input("  Enter your research question:\n  > ").strip()
        if not user_query:
            user_query = "Find the best UK location for a 100 MW AI training data centre"
            print(f"  Using default: {user_query}")

    # ── 2. Preference interview ───────────────────────────────────────────────
    _banner("Step 1 — Preference Interview")
    preferences = collect_user_preferences(user_query, use_llm=not args.no_llm_prefs)
    print("\n  Preferences confirmed.")

    # ── 3. Load policy ────────────────────────────────────────────────────────
    policy = load_policy()
    _print_policy(policy)

    # ── 4. Blueprint generation + approval loop ───────────────────────────────
    _banner("Step 2 — Report Blueprint")
    blueprint = optimise_report_blueprint(user_query, preferences, policy)
    blueprint_approved_first_try = False

    iteration = 0
    while True:
        iteration += 1
        print_blueprint(blueprint)

        approval = input(
            "  Approve this structure? Type 'yes' to continue, or describe changes:\n  > "
        ).strip()

        if approval.lower() in ("yes", "y", "ok", "approve", "approved", ""):
            blueprint_approved_first_try = (iteration == 1)
            print("  Blueprint approved.")
            break

        print("\n  Updating preferences and regenerating blueprint...")
        preferences = update_preferences_from_feedback(preferences, approval)
        blueprint = optimise_report_blueprint(user_query, preferences, policy)

        if iteration >= 5:
            print("  Maximum iterations reached — proceeding with current blueprint.")
            break

    # ── 5. Feature loading + scoring (existing pipeline) ─────────────────────
    _banner("Step 3 — Loading Data & Scoring Candidates")
    print("  Loading geographic features (this may take a moment)...", flush=True)

    budget_gbp = parse_budget_gbp(args.budget) if args.budget else None
    features, diagnostics = load_or_build_features()
    print(f"  Features loaded: {len(features)} candidate regions.")

    constraints = parse_user_constraints(
        prompt=user_query,
        budget_gbp=budget_gbp,
        region=args.region,
        compute_mw=args.compute_mw,
    )
    print(f"  Workload: {constraints.workload} | Region: {constraints.region_text}")

    planning_result = run_planner(features, constraints, args.top_k)
    ranked = add_production_scores(features, constraints)
    print(f"  Scored {len(ranked)} candidates. Top: {ranked.iloc[0]['region']} "
          f"({ranked.iloc[0]['production_score']:.2f}/10)")

    # ── 6. Blueprint-guided agent dispatch ────────────────────────────────────
    _banner("Step 4 — Running Selected Agents")
    print(f"  Agents selected by blueprint: {', '.join(blueprint.agents_to_run)}")
    if blueprint.agents_to_skip:
        print(f"  Skipping: {', '.join(blueprint.agents_to_skip)} (not required by blueprint)")

    runner = AgentRunner(
        model=args.model,
        timeout=args.agent_timeout,
        enabled=not args.no_agents,
    )

    agent_outputs = run_agents_from_blueprint(
        blueprint=blueprint,
        runner=runner,
        user_query=user_query,
        workload=constraints.workload,
        ranked=ranked,
        top_k=args.top_k,
    )
    print(f"  {len(agent_outputs)} agent outputs collected.")

    # ── 7. Compose final report ───────────────────────────────────────────────
    _banner("Step 5 — Composing Report")
    site_result = planning_result.to_dict()

    final_report = compose_final_report(
        user_query=user_query,
        blueprint=blueprint,
        agent_outputs=agent_outputs,
        preferences=preferences,
        site_result=site_result,
    )

    report_path = _save_report(final_report, "blueprint_report.md")
    print(f"  Report saved to: {report_path}")
    print()
    print(final_report)

    # ── 8. Blueprint critic ───────────────────────────────────────────────────
    _banner("Step 6 — Critic Evaluation")
    critic_result = critic_evaluate(final_report, blueprint, preferences)
    print_critic_result(critic_result)

    # ── 9. User acceptance + policy update ───────────────────────────────────
    _banner("Step 7 — Feedback & Policy Update")
    user_feedback = input(
        "\n  Accept this report, or describe what you want changed:\n  > "
    ).strip()
    if not user_feedback:
        user_feedback = "yes"

    updated_policy = update_policy_from_feedback(
        preferences=preferences,
        blueprint=blueprint,
        critic_result=critic_result,
        user_feedback=user_feedback,
        blueprint_approved_first_try=blueprint_approved_first_try,
    )

    print(f"\n  Policy updated: {policy_summary(updated_policy)}")
    print(f"  (Saved to data/policy/blueprint_policy.json)")

    # ── 10. Optional JSON dump ────────────────────────────────────────────────
    if args.json_out:
        output = {
            "query": user_query,
            "preferences": preferences.to_dict(),
            "blueprint": blueprint.to_dict(),
            "site_selection": site_result,
            "agent_outputs": [o.to_dict() for o in agent_outputs],
            "critic": critic_result.to_dict(),
            "updated_policy": updated_policy,
        }
        json_path = _save_report(json.dumps(output, indent=2, default=str), "blueprint_output.json")
        print(f"  JSON output saved to: {json_path}")

    _banner("Run complete")


if __name__ == "__main__":
    main()
