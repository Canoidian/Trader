# Analysis Explorer Handoff Report

## 1. Observation

During the exploration of the Milestone 2 Analysis Engine, I inspected `krakentrader/analysis.py` and `scripts/run_analysis.py`. I observed five specific bugs that correspond to the failure context provided:

1. **Discontinuous RSI scoring logic**: In `analysis.py`, `calculate_composite_score(closes)` assigns `score += 10.0` if `rsi14 < 30` and `score -= 10.0` if `rsi14 > 70`. However, the `else` block interpolates the score with `score += 5.0 - ((rsi14 - 30) / 40.0) * 10.0`. For `rsi14 = 30`, this evaluates to `5.0`, causing a discontinuous 5-point jump from `10.0` to `5.0`.
2. **Python truthiness bug**: In `analysis.py`, line 70 reads `if sma14 and current_price > sma14:`. If `sma14` evaluates exactly to `0.0`, the condition resolves as `False` due to Python truthiness. 
3. **Flat-asset RSI bug**: In `analysis.py`, line 31 checks `if avg_loss == 0: return 100.0`. If an asset's price doesn't change, both `avg_gain` and `avg_loss` evaluate to `0`, resulting in a return value of `100.0` instead of a neutral `50.0`.
4. **Off-by-one inconsistency in constraints**: In `analysis.py`, `calculate_composite_score` returns `0.0` if `len(closes) < 15` (requiring `>= 15`). However, `scripts/run_analysis.py` line 43 checks `if closes and len(closes) > 15:`, effectively requiring `16` or more candles, skipping the case of exactly 15 candles.
5. **Missing timeout on HTTP request**: In `scripts/run_analysis.py`, line 17 reads `with urllib.request.urlopen(req) as response:`. This blocking network call lacks a `timeout` parameter, exposing the script to indefinite hangs.

## 2. Logic Chain

1. **RSI Discontinuity**: To create a continuous scoring function for RSI, the interpolation logic must produce values that match the boundary conditions. Between `30` and `70`, the formula should map `30 -> 10.0` and `70 -> -10.0`. Modifying the interpolation line to `score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0` resolves this.
2. **Truthiness Check**: The value of `0.0` is a valid price/SMA (though rare). Replacing `if sma14` with an explicit `None` check (`if sma14 is not None and current_price > sma14:`) ensures `0.0` is evaluated correctly.
3. **Flat Asset RSI**: A perfectly flat asset implies neither gains nor losses. The `RSI` should logically evaluate to the neutral `50.0`. We can check if `avg_gain == 0` when `avg_loss == 0` and return `50.0`.
4. **Off-by-one Consistency**: `calculate_rsi` with a period of `14` strictly requires at least `15` candles. To align the requirement across the code, the check in `scripts/run_analysis.py` should be updated from `> 15` to `>= 15`.
5. **Network Reliability**: Adding a `timeout` argument to `urlopen` ensures the script fails fast instead of hanging when the API is unresponsive. 

## 3. Caveats

- I assume the intended RSI bounds in `calculate_composite_score` are indeed `+10.0` and `-10.0` as stated in the condition, not `+5.0` and `-5.0`.
- The fixes proposed are localized to the stated bugs and do not refactor the entire logic of SMA/RSI.
- Network mode constraints prevented live endpoint testing for the `urllib` fix, but standard library `urlopen` signatures guarantee `timeout` validity.

## 4. Conclusion

The analysis engine contains logic bugs and inconsistencies that impact scoring accuracy and operational stability. The proposed fix strategy involves straightforward, localized modifications across `krakentrader/analysis.py` and `scripts/run_analysis.py` to restore continuous scoring, correct boolean evaluation, properly handle edge-case flat assets, harmonize list length bounds, and harden network requests. 

**Proposed Changes:**
1. **`krakentrader/analysis.py`**:
   - Change `score += 5.0 - ((rsi14 - 30) / 40.0) * 10.0` to `score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0`.
   - Change `if sma14 and current_price > sma14:` to `if sma14 is not None and current_price > sma14:`.
   - Change `if avg_loss == 0: return 100.0` to:
     ```python
     if avg_loss == 0:
         if avg_gain == 0:
             return 50.0
         return 100.0
     ```
2. **`scripts/run_analysis.py`**:
   - Change `if closes and len(closes) > 15:` to `if closes and len(closes) >= 15:`.
   - Change `urllib.request.urlopen(req)` to `urllib.request.urlopen(req, timeout=10)`.

## 5. Verification Method

- Implement the changes exactly as described above.
- Run `python scripts/run_analysis.py` to ensure it successfully computes scores.
- Create localized unit tests that simulate:
  1. An array of exactly 15 flat values (e.g., `[100.0] * 15`) to verify RSI returns `50.0` and that the `> 15` off-by-one error no longer excludes this case.
  2. Test `current_price > sma14` where `sma14 = 0.0` to verify it evaluates properly.
  3. Verify a computed `RSI` of `30` perfectly scores `+10.0`.
