# Handoff Report

## Observation
1. **Integrity Violation (CLI/CSV Parsing)**: `scripts/run_analysis.py` has been updated to use `argparse` for `--data-dir` and `--coins` in Iteration 3. However, the CSV loading logic `closes = [float(row[4]) for row in reader if len(row) > 4]` throws a `ValueError` because it attempts to parse the CSV header ("close") as a float (`tests/e2e/conftest.py` generates a header). Furthermore, if a coin is missing (which `tests/e2e/test_e2e.py::test_f2_t1_missing_coin_data` specifically tests for), the script prints an error and skips the coin instead of exiting with a non-zero status.
2. **Missing Unit Tests**: Running `find_by_name` on `test_analysis.py` and listing the `tests/` directory reveals that unit tests for `krakentrader/analysis.py` are completely missing.
3. **ZeroDivisionError**: In `krakentrader/analysis.py`, `calculate_sma(closes, period)` and `calculate_rsi(closes, period)` lack protection against `period <= 0`. For example, in `calculate_sma`:
   ```python
   def calculate_sma(closes, period):
       if len(closes) < period:
           return None
       return sum(closes[-period:]) / period
   ```
   If `period = 0`, `len(closes) < 0` is False, and it evaluates `sum(...) / 0`.

## Logic Chain
1. Because `run_analysis.py` does not skip the CSV header, loading fails for *all* valid test data. Adding `next(reader, None)` before iterating over the CSV rows will resolve the `ValueError`.
2. Because E2E tests expect `run_analysis.py` to fail when a coin's data is missing (e.g., `test_f2_t1_missing_coin_data`), we must enforce a fail-fast behavior: if `closes` is None or `< 15`, call `sys.exit(1)`.
3. Because `calculate_sma` and `calculate_rsi` do not validate `period > 0`, they produce a `ZeroDivisionError` on zero/negative input. Adding an explicit guard `if period <= 0: raise ValueError(...)` will fix this vulnerability.
4. Because no unit tests exist, an implementation plan must specify the creation of `tests/test_analysis.py` encompassing edge cases (empty lists, negative periods) and happy paths for `sma`, `rsi`, `volatility`, and `composite_score`.

## Caveats
- I did not run the test suite directly to verify the exact failure output of `run_analysis.py` because the command timeout restrictions prevented running `pytest tests/e2e/`. My analysis relies on statically analyzing the mock data generated in `conftest.py` and the E2E test assertions.

## Conclusion
The Implementer needs to:
1. Update `scripts/run_analysis.py` to correctly skip the CSV header (`next(reader, None)`) and exit with `sys.exit(1)` when any requested coin fails to load or lacks sufficient data.
2. Add input validation guards to `calculate_sma` and `calculate_rsi` in `krakentrader/analysis.py` to raise a `ValueError` when `period <= 0`.
3. Create `tests/test_analysis.py` providing unit tests for all functions in `krakentrader/analysis.py`.

## Verification Method
- **CSV Fix**: Run `python scripts/run_analysis.py --data-dir <some_mock_data_dir> --coins BTC,ETH,SOL` and verify it correctly parses the CSV and outputs rankings.
- **Fail Fast Fix**: Run `pytest tests/e2e/test_e2e.py::test_f2_t1_missing_coin_data` to ensure the analyzer fails appropriately on missing coin files.
- **ZeroDivision Fix**: Call `calculate_sma([1, 2, 3], 0)` and verify it raises a `ValueError` instead of a `ZeroDivisionError`.
- **Unit Tests**: Run `pytest tests/test_analysis.py` and ensure 100% coverage on `krakentrader/analysis.py`.
