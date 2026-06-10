# Handoff Report: Milestone 2 Analysis Engine Bug Fixes

**Summary**: Investigation of the Milestone 2 Analysis Engine (`krakentrader/analysis.py` and `scripts/run_analysis.py`) successfully identified the 5 documented bugs. The root causes range from math logic to Python truthiness and API behavior. A fix strategy has been provided below for implementation.

## 1. Observation

### Bug 1: Discontinuous RSI scoring logic
- **Location**: `krakentrader/analysis.py:76-82`
- **Code**:
  ```python
      # RSI component
      if rsi14 is not None:
          if rsi14 < 30:
              score += 10.0
          elif rsi14 > 70:
              score -= 10.0
          else:
              score += 5.0 - ((rsi14 - 30) / 40.0) * 10.0
  ```

### Bug 2: Python truthiness bug (`if sma14` evaluates to `False` if `sma14 == 0.0`)
- **Location**: `krakentrader/analysis.py:70`
- **Code**:
  ```python
      # Trend component
      if sma14 and current_price > sma14:
  ```

### Bug 3: Flat-asset RSI bug
- **Location**: `krakentrader/analysis.py:31-32`
- **Code**:
  ```python
      if avg_loss == 0:
          return 100.0
  ```

### Bug 4: Off-by-one inconsistency in minimum candle constraints
- **Location 1**: `krakentrader/analysis.py:58` uses `< 15` (meaning `15` is accepted).
- **Location 2**: `krakentrader/analysis.py:5` uses `< period` (where period is 14).
- **Location 3**: `krakentrader/analysis.py:10` uses `<= period` (meaning requires `len >= 15`).
- **Location 4**: `scripts/run_analysis.py:43` uses `> 15` (meaning requires `len >= 16`).

### Bug 5: Missing timeout on HTTP request
- **Location**: `scripts/run_analysis.py:17`
- **Code**:
  ```python
          with urllib.request.urlopen(req) as response:
  ```

## 2. Logic Chain

**Fixing Bug 1 (RSI Discontinuity)**
- **Issue**: For `rsi14 = 30`, the formula `5.0 - (0 / 40.0) * 10.0` yields `5.0`, causing a 5-point drop from the `< 30` condition (`10.0`). For `rsi14 = 70`, the formula yields `-5.0`, causing a 5-point jump to the `> 70` condition (`-10.0`).
- **Strategy**: Modify the interpolation to span the full range from `+10.0` at RSI 30 to `-10.0` at RSI 70.
- **Proposed Change**: Replace the `else` block calculation with:
  ```python
              score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0
  ```

**Fixing Bug 2 (Truthiness)**
- **Issue**: If `sma14` evaluates exactly to `0.0`, the `if sma14` condition will be falsy, deducting 5.0 erroneously. 
- **Strategy**: Explicitly check for `None` since `calculate_sma` returns `None` on insufficient data.
- **Proposed Change**:
  ```python
      if sma14 is not None and current_price > sma14:
  ```

**Fixing Bug 3 (Flat-asset RSI)**
- **Issue**: When an asset is completely flat (all closes are equal), both `avg_gain` and `avg_loss` are `0`. The current code catches `avg_loss == 0` and blindly returns `100.0` (indicating maximum bullishness), which is incorrect for a flat asset.
- **Strategy**: Check if both `avg_gain` and `avg_loss` are zero, returning a neutral RSI of `50.0`. If only `avg_loss` is zero, return `100.0`.
- **Proposed Change**:
  ```python
      if avg_loss == 0:
          if avg_gain == 0:
              return 50.0
          return 100.0
  ```

**Fixing Bug 4 (Off-by-one constraint)**
- **Issue**: The core logic in `analysis.py` allows evaluation if there are `15` candles (since `14` period RSI needs `15` data points to have `14` changes). However, `scripts/run_analysis.py` uses `> 15`, rejecting the valid 15-candle edge case.
- **Strategy**: Standardize the check in `scripts/run_analysis.py` to be `len(closes) >= 15`.
- **Proposed Change**: Update `scripts/run_analysis.py`:
  ```python
          if closes and len(closes) >= 15:
  ```

**Fixing Bug 5 (Missing HTTP timeout)**
- **Issue**: `urllib.request.urlopen` can hang indefinitely without a timeout, causing script failure on poor network.
- **Strategy**: Add a reasonable timeout parameter.
- **Proposed Change**:
  ```python
          with urllib.request.urlopen(req, timeout=10) as response:
  ```

## 3. Caveats
- No actual implementation was performed (adhering to read-only constraints).
- Did not run the scripts directly since no code changes were made yet.

## 4. Conclusion
The five specific errors observed by the Challengers can all be mitigated with isolated logic tweaks. The technical analysis math structures are sound otherwise. An implementation agent can safely apply the Proposed Changes outlined in the Logic Chain to clear the Gate.

## 5. Verification Method
1. **Apply the fixes** provided in the Logic Chain.
2. **Execute the script**: `python scripts/run_analysis.py` to ensure it completes fetching, calculates correctly, and avoids hangs.
3. **Write/Run Unit tests** targeting:
   - A flat list of prices (e.g., `[100] * 20`) to verify RSI returns `50.0`.
   - Exactly 15 prices to ensure no `None` is improperly discarded.
   - Prices where RSI evaluates to boundaries (30 and 70) to ensure the composite score doesn't jump discontinuously.
