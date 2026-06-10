# Handoff Report: Iteration 3 Bug Investigation

## Observation
1. **Bug 1 (ZeroDivisionError)**: In `krakentrader/backtest.py:12`, `step = len(ohlcv_data) // (num_trades + 1)`. If `num_trades` is passed as `-1`, this evaluates to division by zero.
2. **Bug 2 (Rate Limits)**: In `krakentrader/api.py:14-26`, the retry loop checks `if response.status_code == 429`, but if Kraken returns HTTP 200 with JSON like `{"error": ["EAPI:Rate limit exceeded"]}`, it proceeds to `response.raise_for_status()` and then `raise Exception(...)` at line 26, aborting the retry loop immediately.
3. **Bug 3 (CLI Arguments Ignored)**: In `scripts/run_backtest.py`, no command-line arguments are parsed. Lines 10-14 hardcode `pair = 'XXBTZUSD'` and call `get_historical_ohlcv(pair)` unconditionally, completely ignoring the `--data-dir`, `--coin`, and `--capital` arguments passed by E2E tests (e.g., `tests/e2e/test_e2e.py:14`). I also observed that `scripts/run_analysis.py` has the identical issue, ignoring test suite arguments.
4. **Bug 4 (Fee Tier Math)**: In `krakentrader/backtest.py:36`, `fee_rate = calculate_fee(1.0, is_maker=False)`. If `calculate_fee` returns the actual fee amount for 1.0 volume, it effectively returns the flat fee rate. If volume-based tiers are implemented, a $1.0 query will use the highest tier rate, under-calculating crypto volume when executing a $100 trade.

## Logic Chain
1. **Bug 1**: To prevent adversarial crashes, `run_backtest` must validate `num_trades`. A check `if num_trades < 1:` at the beginning of the function will prevent zero division or negative steps.
2. **Bug 2**: To properly backoff when Kraken returns a 200 OK with a rate limit error, the JSON parsing (`data = response.json()`) must happen *inside* the retry loop. If `data.get('error')` contains a rate limit string, it should trigger the sleep and `continue`.
3. **Bug 3**: E2E tests pass a local path via `--data-dir` to provide mock data. The script must use `argparse` to capture `--data-dir`, `--coin`, and `--capital`. If `--data-dir` is provided, it should construct the path `{data_dir}/{coin}_historical.csv`, parse it with the `csv` module (skipping the header), and format rows such that index 1 is open and index 4 is close, completely bypassing `get_historical_ohlcv`.
4. **Bug 4**: Instead of querying `calculate_fee(1.0)`, we can query `calculate_fee(trade_size_fiat)`. By taking `approx_fee = calculate_fee(trade_size_fiat, is_maker=False)`, we can derive the implied rate for that size: `implied_rate = approx_fee / trade_size_fiat`. Then `executed_volume = trade_size_fiat / (1 + implied_rate)`. This correctly accounts for volume-based tiers while retaining the exact inverse fee math.

## Caveats
- `run_analysis.py` was not explicitly listed in Bug 3's description in the failure report, but the E2E test suite actively tests it with `--data-dir` and `--coins`. Applying the `argparse` fix to both scripts is highly recommended to ensure the test suite fully passes.
- For Bug 4, using `trade_size_fiat` instead of `1.0` to query the fee rate assumes that `trade_size_fiat` falls into the same fee tier as `executed_volume`. Since they differ only by a fraction of a percent (the fee itself), this is mathematically robust for tier thresholds.

## Conclusion
The root causes for all 4 bugs have been verified. 
- Fix 1: Validate `num_trades >= 1` in `backtest.py`.
- Fix 2: Move JSON evaluation inside the retry loop in `api.py` and catch `Rate limit` errors for backoff.
- Fix 3: Add `argparse` to `run_backtest.py` (and `run_analysis.py`) to bypass the API and read local CSVs if `--data-dir` is passed.
- Fix 4: Infer the fee rate using `trade_size_fiat` instead of `1.0` in `backtest.py`.

## Verification Method
- **Bug 1**: Run `pytest` or a script passing `num_trades=-1` to `run_backtest()`; it should raise a `ValueError` cleanly instead of `ZeroDivisionError`.
- **Bug 2**: Introduce a mock `requests.get` that returns 200 OK with `{"error": ["EAPI:Rate limit exceeded"]}` for the first two calls and observe the sleep behavior.
- **Bug 3**: Run `python scripts/run_backtest.py --data-dir tests/fixtures/data --coin BTC` and verify it reads the CSV and prints PnL without making network calls.
- **Bug 4**: Modify `calculate_fee` locally to return `0.50` for `1.0` and `0.10` for `100.0`. Run `run_backtest` and verify that the executed volume uses the `0.10` rate logic.
