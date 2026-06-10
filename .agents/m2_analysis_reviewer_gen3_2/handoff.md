# Handoff Report

## 1. Observation
- `scripts/run_analysis.py` hardcodes the pairs: `pairs = ['XXBTZUSD', 'XETHZUSD', 'SOLUSD']`.
- `scripts/run_analysis.py` contains no `argparse` or `sys.argv` parsing. It completely ignores `--data-dir` and `--coins` flags.
- `tests/e2e/test_e2e.py` heavily tests `scripts/run_analysis.py` using CLI arguments, e.g., `run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "BTC,ETH,SOL")`.
- Several tests in `test_e2e.py` (like `test_f2_t1_missing_coin_data` and `test_f2_t1_unsupported_ticker`) assert that `run_analysis.py` will fail (`result.returncode != 0`) when provided with invalid local data or unsupported tickers. Because the script ignores local data flags and runs against the live Kraken API, these tests are guaranteed to fail or produce false positives offline.
- There are no unit tests for the analysis module (no `tests/test_analysis.py`).

## 2. Logic Chain
- The project test infrastructure (`TEST_INFRA.md` and `tests/e2e/test_e2e.py`) explicitly defines the contract that `scripts/run_analysis.py` must accept `--data-dir` and `--coins` to operate on local mock data.
- Because `scripts/run_analysis.py` hardcodes its inputs and behavior (fetching from the live internet), it acts as a facade implementation that bypasses the test suite's inputs. 
- This is a critical interface conformance issue and constitutes an **Integrity Violation** under "dummy or facade implementations that look correct but implement no real logic" regarding the required test-driven CLI interface. The implementation cannot possibly pass the project's offline E2E test suite.

## 3. Caveats
- The core mathematical functions in `krakentrader/analysis.py` (`calculate_sma`, `calculate_rsi`, `calculate_volatility`) are implemented correctly and handle edge cases safely (e.g., division by zero, insufficient data).
- The network environment prevents running `pytest` directly to see the exact test failure output, but static analysis of the source code undeniably confirms the mismatch between the test cases and the script's parameter handling.

## 4. Conclusion
**Verdict**: REQUEST_CHANGES (Critical finding: INTEGRITY VIOLATION)
- The implementation of `scripts/run_analysis.py` is a facade that ignores required test inputs (`--data-dir`, `--coins`) and hardcodes data fetching, making the provided E2E tests impossible to pass correctly. 
- The missing CLI parsing must be implemented to read local CSVs based on `--data-dir`.
- Unit tests for `krakentrader/analysis.py` should be added to ensure completeness.

## 5. Verification Method
- Inspect `scripts/run_analysis.py` line 35-40 to see the lack of `argparse` and hardcoded `pairs` list.
- Inspect `tests/e2e/test_e2e.py` to see the expected CLI interface.
- Run `pytest tests/e2e/test_e2e.py` locally to verify that the E2E tests fail due to the script ignoring arguments.
