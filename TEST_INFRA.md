# E2E Test Infra: KrakenTraderV2

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Execution & Fee Verification | ORIGINAL_REQUEST R1/AC1 | 5      | 5      | ✓      |
| 2 | Research Verification | ORIGINAL_REQUEST R2/AC2 | 5      | 5      | ✓      |

## Test Architecture
- Test runner: `pytest tests/e2e/`
- Test case format: Python `pytest` functions using `subprocess` to run CLI scripts (`scripts/run_backtest.py` and `scripts/run_analysis.py`). Verification through stdout parsing and exit codes.
- Directory layout: `/tests/e2e/`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full automated end-to-end simulation: Analyze coins then backtest top recommendation | F1, F2 | Medium |

## Coverage Thresholds
- Tier 1: ≥5 per feature
- Tier 2: ≥5 per feature (where boundaries exist)
- Tier 3: pairwise coverage of major feature interactions
- Tier 4: ≥5 realistic application scenarios (or logical grouping since only 2 features)
