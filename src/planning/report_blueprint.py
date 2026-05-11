"""Display utilities for ReportBlueprint objects."""
from __future__ import annotations

from ..preferences.schemas import ReportBlueprint

_DEPTH_LABEL = {"short": "brief", "medium": "balanced", "detailed": "in-depth"}


def print_blueprint(blueprint: ReportBlueprint) -> None:
    """Pretty-print the blueprint to stdout for human approval."""
    width = 62
    line = "─" * width

    print(f"\n{'':>2}{'PROPOSED RESEARCH BLUEPRINT':^{width}}")
    print(f"  {line}")
    print(f"  Title : {blueprint.title}")
    print(f"  Goal  : {blueprint.goal}")
    print(f"  {line}")

    print(f"\n  Report sections (in order):")
    for i, section in enumerate(blueprint.sections, 1):
        depth = _DEPTH_LABEL.get(section.depth, section.depth)
        print(f"    {i:>2}. {section.name:<28} [{depth}]")
        print(f"        {section.purpose}")
        if section.required_evidence:
            evidence = ", ".join(section.required_evidence[:4])
            print(f"        Evidence needed: {evidence}")

    print(f"\n  Agents selected : {', '.join(blueprint.agents_to_run)}")
    if blueprint.agents_to_skip:
        print(f"  Agents skipped  : {', '.join(blueprint.agents_to_skip)}")

    print(f"\n  {line}")


def blueprint_to_text(blueprint: ReportBlueprint) -> str:
    """Return a compact text summary of the blueprint (for LLM context)."""
    sections_text = "\n".join(
        f"  - {s.name} [{s.depth}]: {s.purpose}"
        for s in blueprint.sections
    )
    return (
        f"Title: {blueprint.title}\n"
        f"Goal: {blueprint.goal}\n"
        f"Sections:\n{sections_text}\n"
        f"Agents: {', '.join(blueprint.agents_to_run)}\n"
        f"Skipped: {', '.join(blueprint.agents_to_skip)}"
    )
