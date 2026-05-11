from __future__ import annotations

from dataclasses import dataclass

"""CAM'S COMMENTS:
policy.py

    * hardcoded policies? how are these chosen? what do they actually do?
"""


@dataclass(frozen=True)
class PolicyOpportunity:
    name: str
    summary: str
    score_bonus: float
    source_url: str


POLICY_OPPORTUNITIES = [
    PolicyOpportunity(
        "AI Growth Zones",
        "UK programme for AI-enabled data centres that can improve access to power and planning support; applications are open-ended and eligibility is site-specific.",
        1.2,
        "https://www.gov.uk/government/collections/ai-growth-zones",
    ),
    PolicyOpportunity(
        "AI Growth Zone delivery reforms",
        "Policy package includes grid-connection acceleration, planning support, and targeted operating-cost support for qualifying AI Growth Zones.",
        1.0,
        "https://www.gov.uk/government/publications/delivering-ai-growth-zones",
    ),
    PolicyOpportunity(
        "Investment Zone tax sites",
        "Designated Investment Zone tax sites can offer business tax reliefs; candidate-specific eligibility needs GIS validation against official tax-site maps.",
        0.0,
        "https://www.gov.uk/government/collections/maps-of-investment-zones-and-investment-zone-tax-sites",
    ),
    PolicyOpportunity(
        "Freeport and Investment Zone employer NIC relief",
        "Employer Class 1 National Insurance relief may apply in designated Freeport or Investment Zone special tax sites.",
        0.0,
        "https://www.gov.uk/guidance/check-if-you-can-claim-national-insurance-relief-in-freeport-tax-sites",
    ),
    PolicyOpportunity(
        "Freeport SDLT relief",
        "Stamp Duty Land Tax relief may apply for qualifying land purchases in English Freeport tax sites until 30 September 2026.",
        0.0,
        "https://www.gov.uk/government/publications/stamp-duty-land-tax-relief-for-freeports/stamp-duty-land-tax-relief-for-freeports",
    ),
]


def opportunities_for_region(
    region: str, country: str | None = None
) -> list[PolicyOpportunity]:
    return POLICY_OPPORTUNITIES


def policy_score(region: str, country: str | None = None) -> float:
    score = 5.0 + sum(
        opp.score_bonus for opp in opportunities_for_region(region, country)
    )
    return max(0.0, min(10.0, score))


def policy_points(region: str, country: str | None = None) -> list[str]:
    points = []
    for opportunity in opportunities_for_region(region, country):
        points.append(f"{opportunity.name}: {opportunity.summary}")
    return points


def grant_tax_breaks(region: str, country: str | None = None) -> list[str]:
    return [
        f"{opp.name} ({opp.source_url})"
        for opp in opportunities_for_region(region, country)
    ]
