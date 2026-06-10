# Handoff Report: Iteration 4 Bug Investigation

## Observation
I investigated the two bugs reported in the Iteration 3 failure report:

1. **UnboundLocalError on Consecutive HTTP 429 Responses**
   - **Location:** `krakentrader/api.py`, lines 13-28.
   - **Details:** The `get_historical_ohlcv()` function uses a `for attempt in range(3):` loop to retry the API call. If an HTTP 429 status code is received on all 3 attempts, the loop terminates without `break`. The `else:` block of the loop simply executes `pass`. Afterwards, line 28 attempts to evaluate `data.get('error')`. Since `data` is only assigned inside the loop when a successful request occurs (`data = response.json()`), the `data` variable remains unassigned, raising an `UnboundLocalError`.

2. **Fee Tier Threshold Edge Case**
   - **Location:** `krakentrader/backtest.py`, lines 38-41.
   - **Details:** The simulation calculates the `effective_rate` using `trade_size_fiat` (the total available balance for the trade). The backtest assumes `executed_volume_fiat = trade_size_fiat / (1 + effective_rate)`. If `trade_size_fiat` lies exactly at or barely above a fee tier boundary, the `effective_rate` is based on the lower tier. However, the subsequent `executed_volume_fiat` falls slightly below the tier boundary due to the subtracted fee, which means the trade would technically be subject to the higher fee tier in reality. 

## Logic Chain
1. **UnboundLocalError:** The code correctly catches the rate limit, but fails to handle the condition where *all* retries fail. By falling through to code that assumes the request succeeded (i.e., that `data` exists), it crashes. This needs an explicit failure state when retries are exhausted.
2. **Fee Tier Threshold:** The mathematical relationship is `Total Fiat = Volume + Fee`. Since the Kraken API fee tiers are based on the trading volume (the executed amount, not the total fiat spent including the fee), we must determine the fee rate based on `executed_volume_fiat`. Because we don't know the exact `executed_volume_fiat` beforehand, we must derive it or verify it after an initial guess. 

## Caveats
- I did not modify `calculate_fee()` as the prompt requested no implementation. Note that `calculate_fee()` in `api.py` does not currently implement multiple tiers, but the `backtest.py` logic needs to be robust enough to handle the fee tiers explicitly as per the scope.
- The two-step verification strategy for the fee tier assumes that deducting a fee will at most drop the executed volume down by one tier (which is true given typical single-digit percentage fees and widely spaced tiers).

## Conclusion
- **Fix for UnboundLocalError:** In `krakentrader/api.py`, replace the `pass` in the `else:` block of the retry loop with an explicit exception, e.g., `raise Exception("Max retries exceeded due to rate limiting")`. This correctly halts execution and reports the rate limit failure instead of causing a variable scope error.
- **Fix for Fee Tier Edge Case:** In `krakentrader/backtest.py`, implement a two-step calculation for the effective rate. First, calculate an estimated rate using `trade_size_fiat` and derive an initial `executed_volume_fiat`. Then, calculate the fee rate again using that initial `executed_volume_fiat`. If the rate changes (i.e., we fell into a higher-fee tier), update the effective rate and compute the final `executed_volume_fiat`.

## Verification Method
- **UnboundLocalError:** Temporarily modify `krakentrader/api.py` to hardcode `response.status_code = 429` to simulate rate limits. Run `pytest` or the project test suite to verify an exception is raised explicitly with the "Max retries exceeded" message instead of `UnboundLocalError`.
- **Fee Tier Edge Case:** Create a mock `calculate_fee` with a tier boundary (e.g., 0.5% below $1000, 0.2% for $1000 and above). Set `trade_size_fiat = 1000`. Verify that the backtest correctly applies the 0.5% fee rate (since the executed volume would be roughly $995, falling into the lower volume tier).
