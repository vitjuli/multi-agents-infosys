# Systematic Evaluation Report
*Generated: 2026-05-11 15:20 UTC*

## Summary

| Module | Status | Pass Rate | Detail |
|--------|--------|-----------|--------|
| Benchmark Suite | **FAIL** | 20% |  |
| Score Stability | **PASS** | — | Scores identical across 2 runs |
| Workload Ordering | **PASS** | 3/3 |  |
| Ground Truth | **PASS** | — |  |
| Agent Coherence | **PASS** | 100% |  |

---

## Benchmark Suite Details

| Query | Status | Top Recommendation | Workload Inferred | Time |
|-------|--------|-------------------|-------------------|------|
| Scotland AI Training — CO2 | **FAIL** | None | ai_training | 0.15s |
| London Financial — Low Latency | **FAIL** | Leeds / Yorkshire | financial_low_latency | 0.17s |
| Wales Backup — Resilience | **FAIL** | None | backup_disaster_recovery | 0.13s |
| UK-wide Energy Optimised | **PASS** | Leeds / Yorkshire | ai_training | 0.13s |
| England Enterprise Colocation | **FAIL** | None | enterprise_colocation | 0.13s |

**Overall benchmark pass rate: 1/5 (20%)**

## Ground Truth Details

- **Precision@20**: 20% (4 of top-20 are known DC LADs)
- **Cluster coverage**: 4/7 known clusters appear in top-50
- Matched LADs: Leeds / Yorkshire, Manchester, Birmingham / West Midlands, Slough / West London

## Score Stability Details

- Runs compared: 2
- Max deviation: 0.00e+00
- Result: Scores identical across 2 runs

## Workload Ordering Details

- ✓ `ai_training_energy_ordering`: Top site energy=10.00, bottom=6.56
- ✓ `financial_latency_ordering`: Top site hub_dist=0.0 km, bottom=261.3 km
- ✓ `score_range_validity`: All scores in [0, 10]

## Agent Coherence Details

- Agents evaluated: 6
- Agents passed all checks: 6 (100%)
- Fallback agents: 0 (skipped hallucination checks)

- ✓ **EnergyAgent**: 3/4 checks
- ✓ **WaterAgent**: 3/4 checks
- ✓ **ClimateCoolingAgent**: 4/4 checks
- ✓ **LatencyAgent**: 3/4 checks
- ✓ **ResilienceAgent**: 3/4 checks
- ✓ **LandPlanningAgent**: 3/4 checks

---
*Evaluation produced by `tests/eval_runner.py`.*
*Deterministic modules require no API key. Agent coherence requires OPENAI_API_KEY.*