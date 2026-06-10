# Handoff Report: Milestone 1 - Kraken API & Backtest Strategy

## Observation
- The `krakentrader` package and `scripts/` directory currently do not exist in `/Users/williamisaak/Projects/KrakenTraderV2`.
- `SCOPE.md` specifies `krakentrader/api.py` must contain `get_historical_ohlcv(pair)` and `calculate_fee(trade_size)`.
- `SCOPE.md` specifies `krakentrader/backtest.py` must simulate trading and apply fee structures.
- `SCOPE.md` specifies `scripts/run_backtest.py` must run a simulation of at least 10 trades and output final PnL.
- `TEST_INFRA.md` specifies that tests run via `pytest`, verifying CLI behavior via stdout parsing.

## Logic Chain
1. **Dependencies**: Since the requirement is for a "basic API wrapper" and explicit fee calculation, using the standard `requests` library is preferable over a heavy abstraction like `ccxt`. `pytest` is also required for testing.
2. **Historical Data Strategy**: Kraken provides a public unauthenticated endpoint for OHLC data (`GET https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}`). The wrapper can use `requests` to fetch this data, extract the "result" dictionary, and return the list of OHLCV rows for the requested pair.
3. **Fee Calculation Strategy**: Kraken's base spot fee tier is typically 0.25% Maker / 0.40% Taker. The `calculate_fee(trade_size, is_maker=False)` function can implement these base tier rates (or a simple volume tier list) and return the exact fee amount for a given trade size.
4. **Code Layout**: We must create the exact directory structure outlined in `PROJECT.md` to house these components.

## Caveats
- Kraken's public OHLC endpoint has rate limits. A simple backtest script shouldn't hit these, but retries/backoffs are omitted for a "basic" wrapper.
- The 10-trade backtesting strategy logic itself isn't specified in `SCOPE.md`, so a simple dummy strategy (e.g., alternating buy/sell every N periods) will be needed to satisfy the 10-trade Acceptance Criteria.

## Conclusion
**Recommended Implementation Strategy for Worker:**

- **Dependencies**: Create a `requirements.txt` containing `requests` and `pytest`. Do NOT use `ccxt`.
- **Historical Data**: Implement `get_historical_ohlcv(pair, interval=1440)` in `api.py` querying `https://api.kraken.com/0/public/OHLC`.
- **Fees**: Implement `calculate_fee(trade_size, is_maker=False)` in `api.py` applying a 0.40% taker / 0.25% maker rate as the baseline.
- **Layout Requirements**:
  - `requirements.txt`
  - `krakentrader/__init__.py`
  - `krakentrader/api.py`
  - `krakentrader/backtest.py`
  - `scripts/run_backtest.py`
  - `tests/e2e/test_backtest_cli.py`

## Verification Method
1. Install dependencies: `pip install -r requirements.txt`
2. Run the script: `python scripts/run_backtest.py`
   - Should complete without errors.
   - Stdout should contain evidence of at least 10 simulated trades.
   - Stdout should explicitly log fee subtractions for each trade.
   - Stdout should display the final PnL summary.
3. Run tests: `pytest tests/e2e/` to verify ACs are met programmatically.
