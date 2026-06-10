# VICTORY — KrakenTraderV2 Project Complete

**Date**: 2026-06-08  
**All acceptance criteria met. All 29 E2E tests pass.**

---

## What Was Built

A Kraken cryptocurrency trading bot with two core functions:

### 1. Backtesting Engine (`krakentrader/backtest.py` + `scripts/run_backtest.py`)
- Fetches real historical OHLCV data from Kraken's public REST API
- Simulates at least 10 round-trip trades (buy at open, sell at close)
- **Explicitly subtracts Kraken trading fees** for every buy and sell:
  - Taker fee: 0.40% (default)
  - Maker fee: 0.25%
- Outputs a full trade-by-trade PnL log and final balance summary

### 2. Market Analysis Engine (`krakentrader/analysis.py` + `scripts/run_analysis.py`)
- Evaluates at least 3 different coins (default: BTC, ETH, SOL)
- Computes: SMA(14), RSI(14), price volatility
- Produces a **ranked recommendation** table (higher composite score = better buy signal)
- Runs entirely locally — no GPU, no heavy memory requirements (pure Python)

---

## How to Run

**Prerequisites**: Python 3.x with `requests` installed.

```bash
# Using the project venv (already has requests):
/Users/williamisaak/Projects/KrakenTrader/.venv/bin/python scripts/run_backtest.py
/Users/williamisaak/Projects/KrakenTrader/.venv/bin/python scripts/run_analysis.py

# Or install requests and use system python:
pip install requests
python3 scripts/run_backtest.py --coin XXBTZUSD --capital 1000
python3 scripts/run_analysis.py --coins XXBTZUSD,XETHZUSD,SOLUSD
```

**Run all tests:**
```bash
cd /Users/williamisaak/Projects/KrakenTraderV2
/Users/williamisaak/Projects/KrakenTrader/.venv/bin/pytest tests/e2e/test_e2e.py -v
# Result: 29 passed, 0 failed
```

### Script Options

#### `scripts/run_backtest.py`
| Argument | Default | Description |
|---|---|---|
| `--coin` | `BTC` | Coin pair for CSV mode; use Kraken pair name (e.g. XXBTZUSD) for live |
| `--capital` | `1000.0` | Starting capital in USD |
| `--data-dir` | (none) | Path to directory with `{COIN}_historical.csv` files; omit to fetch live |

#### `scripts/run_analysis.py`
| Argument | Default | Description |
|---|---|---|
| `--coins` | `XXBTZUSD,XETHZUSD,SOLUSD` | Comma-separated list of ≥3 coins |
| `--data-dir` | (none) | Path to CSV data directory; omit to fetch live |

---

## Module Architecture

```
krakentrader/
├── api.py       — Kraken REST API wrapper (OHLCV fetch + fee calculation)
├── backtest.py  — Round-trip trade simulator with explicit fee deduction
├── analysis.py  — SMA, RSI, volatility, composite scoring (pure Python)
└── __init__.py

scripts/
├── run_backtest.py  — CLI runner for backtesting
└── run_analysis.py  — CLI runner for analysis & ranking

tests/e2e/
├── test_e2e.py  — 29 E2E tests (all passing)
└── conftest.py  — Fixtures with mock CSV data
```

---

## Test Results (Final)

```
29 passed, 0 failed in 5.91s
```

Coverage includes:
- Fee verification with profitable/unprofitable market scenarios  
- Zero-variance, single-direction, micro-trade edge cases
- Boundary: exact 10 trades, zero capital, high-frequency data
- Analysis with 3–5 coins, minimal data, large data, zero-variance data
- Pairwise: feed analysis output into backtest, concurrent execution, shared directories
- Scenarios: bull, bear, crab market; weekly rebalance loop; fallback behavior
