## 2026-06-08T08:51:19-04:00
You are implementing the E2E test suite for KrakenTraderV2. Your input is the test strategy in /Users/williamisaak/Projects/KrakenTraderV2/.agents/e2e_testing/explorer_3/handoff.md.

Task:
1. Write the complete `pytest` test suite in `/Users/williamisaak/Projects/KrakenTraderV2/tests/e2e/test_e2e.py` covering all 29 test cases defined in the handoff report.
2. The tests must be opaque-box, using `subprocess.run` to execute `scripts/run_backtest.py` and `scripts/run_analysis.py`.
3. Create a `tests/e2e/conftest.py` if needed to automatically generate mock CSV/JSON data files in a temporary directory for the tests to use via a `--data-dir` flag.
4. Note that the target `scripts/` DO NOT EXIST YET. The tests are expected to fail when run (e.g. FileNotFoundError or exit code 1). This is correct.
5. Verify your tests are syntactically valid and discoverable by running `python -m pytest --collect-only tests/e2e`.
6. Write your handoff report to `/Users/williamisaak/Projects/KrakenTraderV2/.agents/e2e_testing/worker/handoff.md` detailing the implemented tests and the output of the collect-only command.
