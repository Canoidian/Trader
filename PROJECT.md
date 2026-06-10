# Project: KrakenTraderV2

## Architecture
- Language: Python
- Modules:
  - `krakentrader/api/`: Interfaces with Kraken REST API for live data and trading.
  - `krakentrader/analysis/`: Lightweight statistical analysis (e.g., RSI, Moving Averages) to rank coins locally without GPU.
  - `krakentrader/backtest/`: Simulates trading over historical data, applying Kraken fee tier structures explicitly.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Kraken API & Backtesting Core | Basic API wrappers, fee calculator, backtesting loop simulating 10 trades on historical data | none | PLANNED |
| 2 | Lightweight Analysis Engine | Technical analysis logic evaluating at least 3 coins locally to output ranked recommendation | none | PLANNED |
| 3 | Final Integration & E2E | Connect components and pass E2E tests verifying ACs | M1, M2 | PLANNED |

## Interface Contracts
### `api` ↔ `backtest`
- Backtester will use `get_historical_ohlcv(pair)` and `calculate_fee(trade_size)`.
### `analysis` ↔ `api`
- Analyzer will fetch recent data for 3 coins using `get_recent_ohlcv(pair)` to generate rankings.

## Code Layout
```
/krakentrader
  __init__.py
  api.py
  analysis.py
  backtest.py
/tests
  ...
scripts/
  run_backtest.py
  run_analysis.py
```
