# E2E Test Suite Implementation - Handoff

## 1. Observation
- The previous implementation of `tests/e2e/test_e2e.py` and `tests/e2e/conftest.py` was rejected due to Critical INTEGRITY VIOLATION involving tautological assertions (`assert p1.returncode is not None`), hardcoded data flow (bypassing output parsing and directly setting `top_coin = "BTC"`), and using `--scenario` flags to instruct the scripts on what to return rather than relying on mock input data.
- The E2E tests are supposed to strictly mimic real production inputs via mock `.csv` data, executing the actual Python scripts as subprocesses to evaluate genuine responses based solely on data configurations.

## 2. Logic Chain
- To achieve genuine tests without bypasses or facades, `conftest.py` was completely rewritten. It now properly leverages Pytest fixtures to dynamically generate mock CSV data (`timestamp,open,high,low,close,volume`) with realistic deterministic price movements corresponding to explicit configurations like "bull", "bear", "crab", "profitable", "unprofitable", and "zero_variance".
- By controlling the generated mock data rather than passing arbitrary flags like `--scenario="profitable"`, we force the application scripts (`run_analysis.py` and `run_backtest.py`) to natively interpret data, ensuring the integrity of the data processing code.
- `test_e2e.py` was rewritten to strictly enforce `assert result.returncode == 0` for all happy paths. If a script does not exist or crashes, `subprocess.run` yields a non-zero code and the test legitimately fails. This satisfies standard TDD constraints.
- Real stdout parsing (`extract_coins_from_output()`) was rigorously enforced for Tier 3 and Tier 4 integration workflows. We parse stdout for actual output tickers and map them back to the caller instead of asserting hardcoded assumptions, testing true pipeline interactions between `run_analysis.py` and `run_backtest.py`.

## 3. Caveats
- Since the implementation scripts do not yet exist, running `pytest tests/e2e/ -v` right now will yield 100% test failures due to missing files (returncode 2). This is by design (TDD outcome).
- The parsing logic looks for specific tickers inside stdout by stripping punctuation. Once the developers actually implement the formatting, they might need to tweak `extract_coins_from_output` if their output is unusually formatted, but standard console output should parse smoothly.
- The default limit of 512MB for testing "lightweight" capabilities is passed via `MEMORY_LIMIT_MB` environment variable which the `run_analysis.py` is expected to honor or the test could be modified to wrap the call with a system-level resource limit block.

## 4. Conclusion
- The E2E test suite has been fundamentally repaired and fully implemented according to the required `explorer_3` Tier 1-4 strategy. 
- All identified Integrity Violations (tautological asserts, `--scenario` bypass flags, hardcoded integration flows) have been eradicated. 

## 5. Verification Method
1. Read the newly implemented test suite: `view_file /Users/williamisaak/Projects/KrakenTraderV2/tests/e2e/test_e2e.py` and `view_file /Users/williamisaak/Projects/KrakenTraderV2/tests/e2e/conftest.py`. Observe the lack of scenario flags and tautological assertions.
2. Run the tests: `pytest tests/e2e/ -v`. Observe that the tests correctly fail when scripts are missing or output cannot be parsed. The failing tests validate that the test harness legitimately waits for proper script implementation.
