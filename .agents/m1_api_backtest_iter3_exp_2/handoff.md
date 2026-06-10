# Iteration 3 Handoff Report - Explorer 2

## 1. Observation
- **ZeroDivisionError**: In `krakentrader/backtest.py:12`, `step = len(ohlcv_data) // (num_trades + 1)`. When `num_trades = -1`, `num_trades + 1` evaluates to 0, raising `ZeroDivisionError`.
- **Rate Limits (Kraken 429 JSON)**: In `krakentrader/api.py:11-26`, the HTTP request retry loop only checks `response.status_code == 429`. However, the response body JSON is evaluated *after* the `for` loop `break` statement. Therefore, a `200 OK` response with `{"error": ["EAPI:Rate limit exceeded"]}` exits the loop without retrying and instantly throws an Exception.
- **CLI Arguments Ignored**: In `scripts/run_backtest.py:10` and `scripts/run_analysis.py:35`, `argparse` is not used. The scripts hardcode pairs and data fetching, ignoring arguments like `--data-dir` and `--coin`/`--coins` passed by `tests/e2e/test_e2e.py`.
- **Future-Proofing Fee Tier Math**: In `krakentrader/backtest.py:36`, `fee_rate = calculate_fee(1.0, is_maker=False)` evaluates the fee for an artificial trade size of $1.0. If `calculate_fee` introduces tiers based on volume, $1.0 will fetch a higher fee rate tier than a typical $100.0 trade, thereby overestimating the fee rate and underestimating the crypto bought.

## 2. Logic Chain
- **ZeroDivisionError**: We must explicitly handle edge cases where `num_trades <= 0`. Returning the initial state early avoids calculations that lead to divide-by-zero.
- **Rate Limits (Kraken 429 JSON)**: Since Kraken embeds rate limit errors in 200 OK responses, we must parse the JSON *within* the retry loop and trigger backoff if the `error` array contains strings matching `"Rate limit exceeded"`.
- **CLI Arguments Ignored**: The E2E tests depend on passing mocked local CSV directories via `--data-dir`. By adding CLI argument parsing (using `argparse`) and reading from `{coin}_historical.csv` when `--data-dir` is provided, we can prevent external API calls during testing. This logic must be applied to both `run_backtest.py` and `run_analysis.py`.
- **Future-Proofing Fee Tier Math**: To accurately determine the fee rate corresponding to the true trade size without a recursive volume-fee lookup, we can estimate the fee using the total `trade_size_fiat`. Evaluating `calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat` accurately reflects the effective fee rate at the correct volume tier.

## 3. Caveats
- For the fee tier fix, applying `calculate_fee` to `trade_size_fiat` (e.g., $100) instead of the slightly smaller post-fee `executed_volume` is a minimal approximation. It's safe since fee tiers are typically broad, but might differ fractionally right at a tier boundary. 
- `scripts/run_analysis.py` was not explicitly listed in the failure report for CLI args, but analysis of `test_e2e.py` reveals it also receives `--data-dir` and `--coins` and currently lacks `argparse`. Applying the CLI fix to both scripts is recommended to ensure complete test suite success.
- Reading from mock CSVs (`[timestamp, open, high, low, close, volume]`) requires adapting to the internal 8-element list format returned by `get_historical_ohlcv` (`[time, open, high, low, close, vwap, volume, count]`).

## 4. Conclusion
The bugs stem from insufficient edge-case handling (zero division, nested API errors, unparsed CLI args) and hardcoded trade volume proxies ($1.0 fee fetch). 
**Worker Action Plan**:
1. `krakentrader/backtest.py`: Add `if num_trades <= 0:` early return at the start of `run_backtest`.
2. `krakentrader/api.py`: Move JSON parsing inside the `get_historical_ohlcv` retry loop and check for rate-limiting errors in `data.get('error')`, triggering `time.sleep` and `continue` if found.
3. `scripts/run_backtest.py` & `scripts/run_analysis.py`: Import `argparse` and implement `--data-dir`, `--coin`/`--coins`, and optionally `--capital`. If `--data-dir` is passed, read the associated CSV files directly instead of triggering API requests.
4. `krakentrader/backtest.py`: Update line 36 to `fee_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat`.

## 5. Verification Method
- **ZeroDivisionError**: Run `pytest tests/` ensuring any tests with zero or negative trades pass cleanly.
- **Rate Limits**: Temporarily mock the Kraken HTTP response to return a 200 OK with the target JSON error format and verify it retries successfully.
- **CLI Arguments**: Run `python scripts/run_backtest.py --data-dir <some_mock_path> --coin BTC` and confirm it does not make outbound network calls.
- **Future-Proofing Fee Math**: Assert `fee_rate` appropriately matches the relative fee amount returned for the actual `trade_size_fiat` argument.
