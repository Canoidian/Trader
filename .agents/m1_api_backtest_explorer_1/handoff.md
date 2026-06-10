# Handoff Report: Milestone 1 API & Backtest Strategy

## 1. Observation
- Read `SCOPE.md` and `PROJECT.md`. The layout specifies `krakentrader/api.py`, `krakentrader/backtest.py`, and `scripts/run_backtest.py`.
- Checked project root: no Python code exists yet.
- Requirement is to implement basic wrappers, explicit fee calculator, and a 10-trade historical backtest.

## 2. Logic Chain
- **Dependencies**: The project only needs simple public REST API access. `ccxt` is heavy and complex, whereas `requests` is standard, lightweight, and perfect for fetching JSON from a single exchange.
- **Historical Data Strategy**: Kraken provides a public, unauthenticated endpoint `GET https://api.kraken.com/0/public/OHLC`. `krakentrader/api.py` should implement `get_historical_ohlcv(pair)` using `requests.get()` to fetch this data.
- **Fee Calculation Strategy**: The milestone asks for explicit fee subtraction. Kraken uses a maker/taker model. `krakentrader/api.py` (or `backtest.py`) should define a `calculate_fee(trade_size, price, is_maker=False)` function implementing the base tier (e.g., 0.25% taker / 0.16% maker).
- **Backtesting Loop**: `scripts/run_backtest.py` should orchestrate this by fetching OHLC data, running a simple simulation that triggers 10 trades, calling the fee calculator for each trade to deduct from the virtual cash balance, and finally outputting the PnL.

## 3. Caveats
- Kraken API pair names are unique (e.g., "XXBTZUSD" rather than "BTC/USD"). The API wrapper needs to accept or map the correct names.
- Since we are fetching public OHLC data, we are limited to the intervals Kraken provides (e.g., 1, 5, 15, 60, 240, 1440).
- The strategy to generate the 10 trades is arbitrary for this milestone (e.g., alternate buy/sell on each candle) just to prove the fee explicitly subtracts and PnL calculates correctly.

## 4. Conclusion
The Implementer should create the base project structure and implement the following:
- `requirements.txt`: Add `requests` and `pytest`.
- `krakentrader/api.py`: Implement `get_historical_ohlcv` using the public Kraken OHLC endpoint, and `calculate_fee` with fixed % based on base tiers.
- `krakentrader/backtest.py`: Backtester state tracking (balance, positions).
- `scripts/run_backtest.py`: A CLI script that ties it all together, simulating exactly 10 trades and printing the required PnL and fee deductions.

## 5. Verification Method
- Code Review: Ensure `requests` is used instead of `ccxt`, and that `calculate_fee` is explicitly called during simulated trades.
- Execution: Run `python scripts/run_backtest.py`. The standard output must clearly list 10 executed trades, the fee for each, and the final PnL.
- Testing: Implement a test in `tests/e2e/test_backtest.py` (as per `TEST_INFRA.md`) that executes the script via subprocess and asserts an exit code of 0 and parses stdout for the presence of 10 trades.
