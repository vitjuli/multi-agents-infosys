from __future__ import annotations


def derive_optimisation_choices_from_blueprint(startup) -> list[str]:
    priorities = getattr(startup.preferences, "primary_priorities", []) or []
    priority_map = {
        "budget": ["cost"],
        "low-carbon": ["co2"],
        "latency": ["latency"],
        "resilience": ["resilience"],
        "land": ["land_use"],
        "energy": ["infrastructure"],
        "policy": ["political_favour"],
    }
    agent_map = {
        "EnergyAgent": ["infrastructure"],
        "ClimateCoolingAgent": ["co2"],
        "LatencyAgent": ["latency"],
        "ResilienceAgent": ["resilience"],
        "LandPlanningAgent": ["land_use", "political_favour"],
    }
    choices: list[str] = []
    for priority in priorities:
        choices.extend(priority_map.get(str(priority), []))
    for agent in getattr(startup.blueprint, "agents_to_run", []) or []:
        choices.extend(agent_map.get(agent, []))
    return list(dict.fromkeys(choices))
