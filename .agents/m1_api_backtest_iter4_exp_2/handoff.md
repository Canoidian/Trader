# Handoff Report: Iteration 4 Bug Investigation

## 1. Observation
**Bug 1: UnboundLocalError in `api.py`**
- In `krakentrader/api.py:13-25`, `get_historical_ohlcv(pair)` uses a retry loop for API requests. 
- If `response.status_code == 429` is hit on all 3 attempts, the loop `continue`s and finishes without `break`.
- The `else:` block of the `for` loop executes `pass` (line 25).
- Execution proceeds to line 28: `if data.get('error'):`. However, since `data = response.json()` was never reached, `data` is unbound, raising `UnboundLocalError`.

**Bug 2: Fee Tier Threshold Edge Case in `backtest.py`**
- In `krakentrader/backtest.py:38`, `effective_rate` is computed using `trade_size_fiat` (the total budget): `effective_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat`.
- At line 39, `executed_volume_fiat` is calculated as `trade_size_fiat / (1 + effective_rate)`.
- If `trade_size_fiat` exactly meets a lower-fee tier threshold (e.g., $50,000), `effective_rate` will reflect that lower tier. 
- However, since `executed_volume_fiat < trade_size_fiat` (due to fees being subtracted), the actual traded volume falls slightly below the threshold, meaning it should be charged at the higher fee tier. The backtester currently fails to account for this drop in volume shifting the trade into a higher tier.

## 2. Logic Chain
**Bug 1**: 
Since a `for...else` block executes its `else` clause when the loop is not terminated by a `break`, reaching the `else` means all 3 retries failed (due to rate limits). Raising an exception directly in the `else` block prevents the code from proceeding to access the uninitialized `data` variable.

**Bug 2**:
Fee tiers are based on executed volume, not the total fiat budget. To fix the edge case without complicated algebra, we can calculate an initial estimate of the executed volume to determine the correct fee tier:
1. Estimate volume: `estimated_volume = trade_size_fiat / (1 + rate_at_budget)`
2. Get the true fee rate for this estimated volume (which correctly falls below the threshold).
3. Recalculate final `executed_volume_fiat` using this true rate.

## 3. Caveats
- The fix for the fee tier assumes that a single iteration of estimating the volume is sufficient to find the correct tier. For standard step-based tier systems where the fee percentage change is small compared to the tier width, one iteration is mathematically sufficient.
- Currently, `calculate_fee` in `api.py` uses flat rates. The edge case only manifests when tier logic is actually implemented inside `calculate_fee`. However, fixing the backtester logic now ensures it behaves correctly once tiers are added.

## 4. Conclusion
**Bug 1 Strategy**: 
Change the `else: pass` block in `krakentrader/api.py:24-25` to `else: raise Exception("Kraken API error: Max retries exceeded due to rate limits")`. This correctly handles the complete failure of retries and inherently prevents the `UnboundLocalError`.

**Bug 2 Strategy**: 
In `krakentrader/backtest.py`, modify the calculation of `effective_rate` and `executed_volume_fiat` to compute an `estimated_volume` first, then derive the `actual_rate` from that estimate, and finally calculate the true `executed_volume_fiat`.

## 5. Verification Method
- **Bug 1**: Add a mock to `requests.get` to always return an HTTP 429 status code. Call `get_historical_ohlcv()`. It should raise the "Max retries exceeded" exception instead of an `UnboundLocalError`.
- **Bug 2**: To verify, one could temporarily implement a mock fee tier in `calculate_fee` (e.g., `< $50,000 = 0.40%`, `>= $50,000 = 0.20%`). Running the backtester with a budget of exactly $50,000 should apply the `0.40%` tier, since the post-fee executed volume is below $50,000.
