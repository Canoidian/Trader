# Handoff Report

## 1. Observation
I reviewed the E2E test suite in `tests/e2e/test_e2e.py` and `conftest.py`. The suite contains 29 tests structured to cover the tiers specified in `TEST_INFRA.md`.
However, I observed the following critical issues:
- **Scenario Flags**: Tests pass a `--scenario <name>` argument to the CLI scripts (e.g., `run_script(SCRIPT_BACKTEST, "--data-dir", str(mock_data_dir), "--scenario", "profitable")` on line 15, as well as `unprofitable`, `zero_trades`, `hft`, etc.).
- **Tautological Assertions**: In several tests, the assertions check if the return code is not None (e.g., `assert p1.returncode is not None` on line 147, and similar in lines 153-154, 179-180). `subprocess.run` and `Popen.wait` always return an integer, making these assertions trivially true regardless of script failure.
- **Hardcoded Integration**: In `test_f1f2_t3_feed_top_rank` (line 128), the test comments `# Simulate parsing analysis_res.stdout for top rank` and hardcodes `top_coin = "BTC"` instead of actually parsing the output from `SCRIPT_ANALYSIS`.
- **Static Mock Data**: `conftest.py` generates identical, monotonically increasing price data for all coins and scenarios, relying entirely on the `--scenario` flag to vary script behavior instead of varying the input data.

## 2. Logic Chain
- The test suite is defined as an "Opaque-box, requirement-driven" integration test. Real production scripts for a backtester/analyzer should not contain test-specific "scenario" flags.
- By injecting `--scenario` flags, the test suite is actively enabling and encouraging a facade implementation where the script just reads the flag and prints expected output (e.g., `if args.scenario == "profitable": print("PnL: 100")`), completely bypassing real logic. This is an **Integrity Violation**.
- The `is not None` assertions mean that those tests will pass even if the scripts crash or don't exist. This is a fabricated verification that falsely inflates test coverage without providing any real safety.
- Hardcoding `top_coin = "BTC"` defeats the purpose of an integration test, as it breaks the data flow between the two scripts.

## 3. Caveats
- The prompt mentioned "They will fail because the scripts aren't written yet, which is expected." While the tests checking `returncode == 0` will indeed fail as expected, the tests with `is not None` will paradoxically *pass* even though the scripts don't exist.
- `ORIGINAL_REQUEST.md` was not found in the repository, but the requirement intent is clear from `TEST_INFRA.md` and `PROJECT.md`.

## 4. Conclusion
**Verdict**: REQUEST_CHANGES (Critical - INTEGRITY VIOLATION)

The E2E test suite does not actually verify the system and instead provides an explicit avenue for cheating. The tests must be rewritten to:
1. Remove all `--scenario` flags. Script behavior must be driven by the data in the CSVs, not by cheat-flags.
2. Provide dynamic mock data in `conftest.py` (e.g., create specific fixtures for profitable data, unprofitable data, zero variance data) so the scripts naturally behave as expected.
3. Replace all `is not None` assertions with proper validation (e.g., `== 0` for success).
4. Actually parse the output in integration tests instead of hardcoding intermediate values like `"BTC"`.

## 5. Verification Method
- Run `pytest tests/e2e/test_e2e.py` manually. Notice that `test_f1f2_t3_concurrent_execution` and others pass immediately despite the scripts not existing, proving the assertions are tautological.
- Inspect `tests/e2e/test_e2e.py` for the `--scenario` flag to confirm it is used to bypass data-driven testing.
