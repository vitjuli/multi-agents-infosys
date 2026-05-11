"""Fixed benchmark test cases for systematic validation.

Five canonical queries with verifiable expected properties.
All designed to run in --no-agents mode for speed and reproducibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BenchmarkCase:
    name: str
    query: str
    expected_workload: str
    expected_region_scope: str          # "uk" | "country" | "city"
    budget: str | None = None
    region: str | None = None
    compute_mw: float | None = None
    # Checks
    expected_top_country: str | None = None   # top recommendation must be in this country
    min_recommendations: int = 1              # at least N recommendations returned
    score_range: tuple[float, float] = (0.0, 10.0)  # all scores within this range
    expected_feasibility: bool | None = None  # None = don't check


BENCHMARK_CASES: list[BenchmarkCase] = [
    BenchmarkCase(
        name="Scotland AI Training — CO2",
        query="Find the best locations in Scotland for a 100 MW AI training data centre, optimise for low carbon and renewable energy",
        expected_workload="ai_training",
        expected_region_scope="country",
        region="Scotland",
        compute_mw=100.0,
        expected_top_country="Scotland",
        min_recommendations=1,
    ),
    BenchmarkCase(
        name="London Financial — Low Latency",
        query="20 MW low-latency financial trading data centre near London",
        expected_workload="financial_low_latency",
        expected_region_scope="city",
        compute_mw=20.0,
        expected_top_country="England",
        min_recommendations=1,
    ),
    BenchmarkCase(
        name="Wales Backup — Resilience",
        query="50 MW backup and disaster recovery site in Wales, prioritise resilience and flood safety",
        expected_workload="backup_disaster_recovery",
        expected_region_scope="country",
        region="Wales",
        compute_mw=50.0,
        expected_top_country="Wales",
        min_recommendations=1,
    ),
    BenchmarkCase(
        name="UK-wide Energy Optimised",
        query="Find UK-wide locations for 200 MW AI training, optimise for renewable energy capacity",
        expected_workload="ai_training",
        expected_region_scope="uk",
        compute_mw=200.0,
        expected_top_country=None,          # UK-wide, no country constraint
        min_recommendations=1,
    ),
    BenchmarkCase(
        name="England Enterprise Colocation",
        query="60 MW enterprise colocation in England with good latency and political support, budget £500m",
        expected_workload="enterprise_colocation",
        expected_region_scope="country",
        region="England",
        compute_mw=60.0,
        budget="£500m",
        expected_top_country="England",
        min_recommendations=1,
    ),
]
