# Handoff Report

## 1. Observation
- `PROJECT.md` and `SCOPE.md` define an architecture with `krakentrader/api.py` and `krakentrader/backtest.py`.
- The current filesystem shows no Python source code exists yet (`/krakentrader/`, `tests/`, and `scripts/` are missing).
- The requirements state the backtester must use `get_historical_ohlcv(pair)` and `calculate_fee(trade_size)` from the API module.
- The backtesting script must simulate at least 10 trades using historical data, applying Kraken fee structures explicitly.

## 2. Logic Chain
- Since no Python code exists, we must set up the baseline layout.
- For interacting with Kraken's REST API, the `requests` library is the most straightforward option, avoiding heavier dependencies like `ccxt` since we only need a couple of specific endpoints (public OHLC) and explicit fee tier calculation.
- **Historical Data Strategy:** We will use Kraken's public OHLC endpoint: `https://api.kraken.com/0/public/OHLC`. We will query standard pairs (e.g., `XXBTZUSD` or `XBTUSD`) and parse the resulting JSON array (which contains `[time, open, high, low, close, vwap, volume, count]`).
- **Fee Calculation Strategy:** Kraken applies a maker/taker fee schedule based on 30-day rolling volume. The base tier (0-$10k) typically applies a ~0.40% taker fee and ~0.25% maker fee. We will build a hardcoded fee tier lookup table in `api.py`. `calculate_fee(trade_size)` can default to base tier taker fees, or accept parameters for volume and maker/taker type, to compute the exact fee amount: `fee_amount = trade_size_in_base_asset * execution_price * fee_percentage`.
- **Layout of Code Changes:**
  - Create `/requirements.txt` containing `requests`.
  - Create `/krakentrader/__init__.py`.
  - Create `/krakentrader/api.py` (with `get_historical_ohlcv` and `calculate_fee`).
  - Create `/krakentrader/backtest.py` (containing the loop for 10 trades over the fetched OHLC data).
  - Create `/scripts/run_backtest.py` (CLI entry point).

## 3. Caveats
- Kraken's OHLC endpoint limits the amount of returned historical data (typically the last 720 intervals). This is more than enough for simulating 10 trades.
- Fee structures change occasionally on Kraken; the static lookup table will need manual updates if fees change, but satisfies the explicit calculation requirement.

## 4. Conclusion
The worker should implement the components utilizing standard `requests`. No external CCXT dependency is needed. We will pull directly from Kraken's public OHLC API and implement a simple lookup table for their volume-based fee tiers. 

## 5. Verification Method
- After implementation, verify by running `python scripts/run_backtest.py`.
- Ensure it successfully downloads data, prints out at least 10 simulated trades, and displays a final PnL with explicit fee deductions.
- Check that `requests` is the only external network dependency added.
