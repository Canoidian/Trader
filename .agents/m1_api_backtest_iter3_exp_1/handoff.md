# Handoff Report

## Observation
1. **ZeroDivisionError**: In `krakentrader/backtest.py:12`, `step = len(ohlcv_data) // (num_trades + 1)`. If `num_trades` is `-1`, this calculation causes division by zero.
2. **Rate Limits**: In `krakentrader/api.py:13-22`, the retry loop immediately breaks on HTTP 200 responses. JSON-based errors (e.g. `{"error": ["EAPI:Rate limit exceeded"]}`) are checked on lines 25-26 *after* the loop, bypassing the retry logic completely.
3. **CLI Arguments**: In `scripts/run_backtest.py:11`, `pair` is hardcoded to `'XXBTZUSD'`. `sys.argv` is not read at all. E2E tests in `tests/e2e/test_e2e.py` run this script with arguments like `--data-dir`, `--coin`, and `--capital`. Additionally, `test_f1_t2_zero_capital` asserts the script fails with return code `!= 0` if `--capital 0` is passed.
4. **Fee Tier Math**: In `krakentrader/backtest.py:36`, `fee_rate = calculate_fee(1.0, is_maker=False)`. It uses `$1.0` as the trade volume to derive the fee rate, which will miscalculate the rate when volume-based tiers are introduced.

## Logic Chain
1. **ZeroDivisionError**: Adding a check to ensure `num_trades > 0` will prevent the `ZeroDivisionError` and gracefully handle invalid trade configurations.
2. **Rate Limits**: Moving the `data = response.json()` parsing and `error` key check *inside* the retry loop will allow the client to detect rate limit errors within HTTP 200 responses and properly trigger `time.sleep` and `continue`. If the max retries are hit, an exception should be thrown.
3. **CLI Arguments**: The `run_backtest.py` script needs `argparse` to process `--data-dir`, `--coin` (default 'BTC'), and `--capital` (default 1000.0). When `--data-dir` is present, it should skip the API call and read `[args.data_dir]/[args.coin]_historical.csv` using the built-in `csv` module. To satisfy `test_f1_t2_zero_capital`, the script should `sys.exit(1)` if `args.capital <= 0`.
4. **Fee Tier Math**: Since the mathematical logic requires a rate (not an absolute value), we can compute it accurately for the *actual* trade volume by using `fee_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat`. This ensures the exact volume-based tier is applied securely to the calculation.

## Caveats
- The failure report only explicitly mentioned `scripts/run_backtest.py` ignoring arguments. However, `scripts/run_analysis.py` *also* ignores arguments (`--data-dir`, `--coins`) which will cause E2E tests for Feature 2 to fail. The implementer may need to apply the `argparse` fix to `run_analysis.py` as well.
- The `csv` module should skip the header row (`next(reader)`) when parsing mock data since E2E mock data includes a header.
- For `run_backtest.py`, if `--data-dir` is not provided and API is used, ensure the `pair` uses Kraken's naming convention (e.g. `XXBTZUSD` for BTC).

## Conclusion
The bugs can be resolved effectively by implementing the following changes:
- `backtest.py`: Add `if num_trades <= 0: raise ValueError(...)` before calculating `step`.
- `backtest.py`: Change `fee_rate = calculate_fee(1.0, ...)` to `fee_rate = calculate_fee(trade_size_fiat, ...) / trade_size_fiat`.
- `api.py`: Move `response.json()` and `error` checks into the retry loop. Look for `"Rate limit"` inside the error list to trigger retries.
- `run_backtest.py`: Import `argparse` and `csv`. Add CLI flags `--data-dir`, `--coin`, and `--capital`. Add an early exit if `capital <= 0`. Load from CSV if `--data-dir` is provided.

## Verification Method
To verify, an implementer should execute the project test suite after making these changes:
- Valid Input tests: Run `pytest /Users/williamisaak/Projects/KrakenTraderV2/tests/e2e/test_e2e.py::test_f1_t1_profitable_run`
- Invalid Inputs: Run `python /Users/williamisaak/Projects/KrakenTraderV2/scripts/run_backtest.py --capital 0` (should exit `!= 0`)
- Run all tests: `pytest /Users/williamisaak/Projects/KrakenTraderV2`
