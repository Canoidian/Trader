# Scope: M1_Kraken_API_Backtest

## Architecture
- `krakentrader/api.py`: Interfaces with Kraken REST API. Needs `get_historical_ohlcv(pair)` and `calculate_fee(trade_size)`. 
- `krakentrader/backtest.py`: Simulates trading over historical data, applying Kraken fee tier structures explicitly.
- `scripts/run_backtest.py`: Backtesting script that simulates at least 10 trades using historical Kraken data, explicitly subtracts Kraken trading fees for each trade, and outputs a final PnL summary.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1 | Basic API wrappers, fee calculator, backtesting loop simulating 10 trades on historical data | none | PLANNED |

## Interface Contracts
### `api` ↔ `backtest`
- Backtester will use `get_historical_ohlcv(pair)` and `calculate_fee(trade_size)`.
