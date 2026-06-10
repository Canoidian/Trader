# Handoff Report: Milestone 2 Bug Fixes

## 1. Observation
- **Bug 1 (Discontinuous RSI)**: In `krakentrader/analysis.py:75-82`, the scoring logic jumps erratically. `rsi14 = 30` triggers the `else` block: `score += 5.0 - ((30 - 30) / 40.0) * 10.0` which adds `5.0`. But `rsi14 = 29.9` triggers the `< 30` block, which adds `10.0`. Same discontinuous jump at `70`.
- **Bug 2 (Truthiness Bug)**: In `krakentrader/analysis.py:70`, the check `if sma14 and current_price > sma14:` will evaluate `sma14 == 0.0` as falsy, unintentionally skipping the trend logic.
- **Bug 3 (Flat-asset RSI)**: In `krakentrader/analysis.py:31-32`, if `avg_loss == 0`, it unconditionally returns `100.0`, even if `avg_gain == 0` (which should mean RSI is 50.0 for a completely flat asset).
- **Bug 4 (Off-by-one Min Candles)**: In `scripts/run_analysis.py:43`, it requires `len(closes) > 15` (meaning minimum 16 candles). However, `krakentrader/analysis.py:58` `calculate_composite_score` requires `len(closes) < 15` to return early (meaning minimum 15 candles). `calculate_rsi` also allows 15 candles (`len(closes) <= 14` returns None).
- **Bug 5 (Missing Timeout)**: In `scripts/run_analysis.py:17`, `urllib.request.urlopen(req)` is called without a timeout parameter.

## 2. Logic Chain
- **Fixing Bug 1**: The linear interpolation in the `else` block must bridge `+10.0` at RSI 30 to `-10.0` at RSI 70. The formula `score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0` perfectly covers this range continuously without jumps.
- **Fixing Bug 2**: Use explicit `is not None` check to ensure `0.0` is treated as a valid float for SMA comparisons.
- **Fixing Bug 3**: Before returning `100.0` for `avg_loss == 0`, check if `avg_gain == 0`. If both are zero (flat asset), the RSI is perfectly neutral, so return `50.0`.
- **Fixing Bug 4**: Change the condition in `scripts/run_analysis.py` to `len(closes) >= 15` to synchronize with the `calculate_composite_score` logic, ensuring consistency across the codebase.
- **Fixing Bug 5**: Add `timeout=10` to `urlopen` to prevent hanging requests in the background.

## 3. Caveats
- No caveats. The fixes are straightforward and address the specific bugs identified in the prompt. I assumed 10 seconds is a reasonable timeout for the Kraken API.

## 4. Conclusion
Apply the following direct fixes:
- `krakentrader/analysis.py`:
  - Line 82: `score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0`
  - Line 70: `if sma14 is not None and current_price > sma14:`
  - Lines 31-32: Add `if avg_gain == 0: return 50.0` before returning `100.0`.
- `scripts/run_analysis.py`:
  - Line 43: `if closes and len(closes) >= 15:`
  - Line 17: `with urllib.request.urlopen(req, timeout=10) as response:`

## 5. Verification Method
- **Bug 1-3**: Run a unit test script or interactive python session with mocked `closes` data to verify RSI continuity, `sma14=0.0` behavior, and flat-asset handling.
- **Bug 4-5**: Verify the edits in the specific lines with `cat` and run `python3 scripts/run_analysis.py` to ensure it executes successfully without error and respects the timeout and constraints.
