from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict
import warnings

from langgraph.graph import END, START, StateGraph

from src.preferences.interview import collect_user_preferences, update_preferences_from_feedback
from src.planning.blueprint_optimizer import optimise_report_blueprint
from src.planning.report_blueprint import print_blueprint
from src.rl.blueprint_policy import load_policy, policy_summary
from src.rl.memory import memory_summary

warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change in a future version.*",
)


@dataclass
class BlueprintStartupResult:
    user_query: str
    preferences: object
    policy: dict
    blueprint: object
    approved_first_try: bool


class BlueprintStartupState(TypedDict, total=False):
    user_query: str
    use_llm_preferences: bool
    interactive: bool
    preferences: object
    policy: dict
    blueprint: object


def banner(text: str, width: int = 64) -> None:
    print(f"\n{'━' * width}")
    print(f"  {text}")
    print(f"{'━' * width}")


def _collect_preferences_node(state: BlueprintStartupState) -> BlueprintStartupState:
    preferences = collect_user_preferences(
        state["user_query"],
        use_llm=state["use_llm_preferences"],
        interactive=state["interactive"],
    )
    return {"preferences": preferences}


def _optimise_blueprint_node(state: BlueprintStartupState) -> BlueprintStartupState:
    policy = load_policy()
    blueprint = optimise_report_blueprint(
        state["user_query"],
        state["preferences"],
        policy,
    )
    return {"policy": policy, "blueprint": blueprint}


def _build_startup_graph():
    graph = StateGraph(BlueprintStartupState)
    graph.add_node("collect_preferences", _collect_preferences_node)
    graph.add_node("optimise_blueprint", _optimise_blueprint_node)
    graph.add_edge(START, "collect_preferences")
    graph.add_edge("collect_preferences", "optimise_blueprint")
    graph.add_edge("optimise_blueprint", END)
    return graph.compile()


_STARTUP_GRAPH = _build_startup_graph()


def run_blueprint_startup(
    user_query: str | None,
    *,
    use_llm_preferences: bool = True,
    interactive: bool = True,
    default_query: str = "Find the best UK location for a 100 MW AI training data centre",
) -> BlueprintStartupResult:
    banner("Preference-Guided Research Blueprint System")
    print("  UK AI Data Centre Site Selection | Hackathon Demo")
    print(f"  Memory: {memory_summary()}")

    if user_query:
        query = user_query
        print(f"\n  Query: {query}")
    elif interactive:
        print()
        query = input("  Enter your research question:\n  > ").strip()
        if not query:
            query = default_query
            print(f"  Using default: {query}")
    else:
        query = default_query
        print(f"\n  Query: {query}")

    banner("Step 1 — Preference Interview")
    startup_state = _STARTUP_GRAPH.invoke(
        {
            "user_query": query,
            "use_llm_preferences": use_llm_preferences,
            "interactive": interactive,
        }
    )
    preferences = startup_state["preferences"]
    print("\n  Preferences confirmed.")

    policy = startup_state["policy"]
    print(f"\n  Active policy weights: {policy_summary(policy)}")

    banner("Step 2 — Report Blueprint")
    blueprint = startup_state["blueprint"]

    if not interactive:
        print_blueprint(blueprint)
        print("  Blueprint auto-approved for non-interactive CLI run.")
        return BlueprintStartupResult(
            user_query=query,
            preferences=preferences,
            policy=policy,
            blueprint=blueprint,
            approved_first_try=True,
        )

    approved_first_try = False
    iteration = 0
    while True:
        iteration += 1
        print_blueprint(blueprint)

        try:
            approval = input(
                "  Approve this structure? Type 'yes' to continue, or describe changes:\n  > "
            ).strip()
        except EOFError:
            approval = "yes"
            print("  No stdin available: blueprint approved.")

        if approval.lower() in ("yes", "y", "ok", "approve", "approved", ""):
            approved_first_try = iteration == 1
            print("  Blueprint approved.")
            break

        print("\n  Updating preferences and regenerating blueprint...")
        preferences = update_preferences_from_feedback(preferences, approval)
        blueprint = optimise_report_blueprint(query, preferences, policy)

        if iteration >= 5:
            print("  Maximum iterations reached — proceeding with current blueprint.")
            break

    return BlueprintStartupResult(
        user_query=query,
        preferences=preferences,
        policy=policy,
        blueprint=blueprint,
        approved_first_try=approved_first_try,
    )
