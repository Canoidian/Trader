# Iteration 2 Failure Report

The Forensic Auditor reported a CLEAN verdict.
Reviewers 1 and 2 APPROVED the code.

However, Challengers and the Auditor found the following functional bugs:
1. **ZeroDivisionError**: An adversarial input of `num_trades = -1` will trigger a `ZeroDivisionError` due to the calculation `len(ohlcv_data) // (num_trades + 1)`.
2. **Rate Limits (Kraken 429 JSON)**: The 429 backoff implementation only retries on HTTP 429 status codes. Kraken commonly returns rate limit errors within the JSON response body with an HTTP 200 OK (e.g., `{"error": ["EAPI:Rate limit exceeded"]}`). The current logic exits the loop immediately on 200 OK and throws an exception, bypassing the retry mechanism.
3. **CLI Arguments Ignored**: The `run_backtest.py` script completely ignores the test suite's `--data-dir` arguments, causing it to always use live data and bypass the mock data, breaking tests that expect mock data.
4. **Future-Proofing Fee Tier Math**: The code determines the budget-allocated buy rate using `fee_rate = calculate_fee(1.0, is_maker=False)`. While mathematically sound for the current flat-rate implementation, it will break when volume-based tiers are introduced. (A $1.0 trade query would retrieve a higher tier rate than the actual trade, under-calculating crypto amounts).

Please investigate the codebase to fix these bugs and improve the overall robustness.
