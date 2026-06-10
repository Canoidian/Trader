# Handoff Report: Milestone 2 Fix Strategy

## 1. Observation
- `scripts/run_analysis.py` currently has basic `argparse` implemented, but its CSV loading logic (`closes = [float(row[4]) for row in reader if len(row) > 4]`) is brittle and will crash with `ValueError` if a header row is present. If it crashes, it calls `sys.exit(1)`, failing the e2e tests.
- `tests/test_analysis.py` does not exist in the codebase.
- In `krakentrader/analysis.py`, both `calculate_sma` and `calculate_rsi` lack safeguards for `period <= 0`. If `period=0`, `calculate_sma` evaluates `sum(closes[-0:]) / 0`, raising a `ZeroDivisionError`.

## 2. Logic Chain
1. **Integrity Violation (CLI & CSV Loading)**: The prompt indicates an integrity violation due to ignored CLI args. While `argparse` is present in the current code, its CSV loading lacks header skipping. The fix must ensure `sys.argv` is properly respected and that CSV parsing is robust (e.g., catching `ValueError` on float conversion to skip headers).
2. **Missing Unit Tests**: The file `tests/test_analysis.py` is entirely missing. We must create this file and use `pytest` to verify the core math functions (`calculate_sma`, `calculate_rsi`, `calculate_volatility`, `calculate_composite_score`).
3. **ZeroDivisionError**: The functions `calculate_sma` and `calculate_rsi` must return `None` immediately if `period <= 0` to prevent division by zero during average calculations.

## 3. Caveats
- I did not test the CSV files directly, but standard Kraken CSVs or the test suite CSVs often contain a header (like `time, open, high, low, close...`). Robust float conversion is standard practice.
- `calculate_composite_score` requires at least 15 elements to avoid returning `0.0`. Unit tests must provide lists of sufficient length to adequately test scoring.

## 4. Conclusion
The Implementer needs to execute three specific changes:
1. **Fix `scripts/run_analysis.py`**: Update the CSV parsing block inside `if args.data_dir:` to safely skip non-numeric headers:
   ```python
   closes = []
   for row in reader:
       if len(row) > 4:
           try:
               closes.append(float(row[4]))
           except ValueError:
               pass
   ```
2. **Fix `krakentrader/analysis.py`**: Add `if period <= 0: return None` at the top of `calculate_sma` and `calculate_rsi`.
3. **Create `tests/test_analysis.py`**: Implement a suite of unit tests for `krakentrader.analysis`, explicitly testing the `period=0` cases to confirm the `ZeroDivisionError` is resolved.

## 5. Verification Method
1. Run `pytest tests/test_analysis.py` to verify unit tests pass and `ZeroDivisionError` is absent.
2. Run `pytest tests/e2e/test_e2e.py` to ensure `run_analysis.py` successfully parses test suite CSVs and arguments without integrity violations or crashes.
