# Scope: Milestone 2 - Lightweight Analysis Engine

## Architecture
- `krakentrader/analysis.py`: Lightweight statistical analysis (e.g., RSI, Moving Averages, Volatility) to rank coins locally without GPU.
- `scripts/run_analysis.py`: Script that evaluates at least 3 coins locally and outputs a ranked recommendation.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Lightweight Analysis Engine | Technical analysis logic evaluating at least 3 coins locally to output ranked recommendation. Must run without high memory/GPU. | none | PLANNED |

## Interface Contracts
### `analysis` ↔ `api`
- Analyzer will fetch recent data for 3 coins. It expects `get_recent_ohlcv(pair)` to provide data, or it will use its own simple data fetching from Kraken public API for testing purposes to ensure the script runs completely locally and successfully.

## Code Layout
```
/krakentrader
  analysis.py
scripts/
  run_analysis.py
```
