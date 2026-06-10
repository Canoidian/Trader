# Explorer 3 Handoff Report

## Observation
1. **`UnboundLocalError` in `api.py`**
   - **File**: `krakentrader/api.py`, lines 13-28.
   - **Finding**: A `for` loop attempts an API request up to 3 times. On `HTTP 429`, it sleeps and uses `continue`. If all 3 attempts fail with 429, the `else` block on the `for` loop executes, which currently just contains `pass` (line 25). The loop exits without `data` ever being assigned. Subsequently, line 28 attempts to evaluate `if data.get('error'):`, throwing a fatal `UnboundLocalError`.

2. **Fee Tier Threshold Edge Case in `backtest.py`**
   - **File**: `krakentrader/backtest.py`, lines 38-41.
   - **Finding**: `effective_rate` is derived by passing the total fiat budget (`trade_size_fiat`) to `calculate_fee()`. The code then calculates `executed_volume_fiat` by dividing by `(1 + effective_rate)`. Next, `buy_fee` is recalculated using `calculate_fee(executed_volume_fiat)`. Because `executed_volume_fiat < trade_size_fiat`, the executed volume can fall into a higher-fee tier than the total budget. This causes `executed_volume_fiat + buy_fee` to exceed the available `trade_size_fiat`.

## Logic Chain
1. **`api.py` Issue**: In Python, a variable initialized only inside a loop or conditional block is not bound in the local scope if that block is bypassed. Since `data = response.json()` is completely skipped when hitting consecutive `429`s, the reference to `data` on line 28 throws an `UnboundLocalError`.
2. **`backtest.py` Issue**: Fee tiers decrease as trading volume goes up. If the budget (`trade_size_fiat`) is exactly on a tier boundary (e.g. $50,000), it benefits from the lower fee rate. Subtracting this assumed fee gives an actual volume slightly under the threshold (e.g. $49,900), which falls into the more expensive tier. The backtester then recalculates the fee based on this smaller volume and higher rate, but doesn't adjust the volume down to account for the larger fee. Thus, the simulated cost is higher than the available fiat balance, violating accounting logic.

## Caveats
- `api.py` does not currently implement multiple fee tiers in `calculate_fee()`, so the edge case in `backtest.py` only surfaces mathematically when the `calculate_fee` logic is actually updated with volume-based tiers. However, fixing the mathematical formula now is necessary to satisfy the requirements.
- We assume `trade_size_fiat` represents the *inclusive* budget for the trade (executed volume + fees).

## Conclusion
- **Fix strategy for `api.py`**: Update the `else:` block of the `for` loop (line 24) to raise a specific exception (e.g., `raise Exception("Max retries exceeded due to rate limiting")`). This halts execution safely before line 28 is reached, entirely preventing the `UnboundLocalError`.
- **Fix strategy for `backtest.py`**: Update the `executed_volume_fiat` calculation to account for the tier shift. Use the initial rate as a guess to find a preliminary volume. Then, calculate the fee rate for that preliminary volume. If the rate has increased (tier changed), do a one-time recalculation of the volume using the new actual rate.
  *Conceptual implementation:*
  ```python
  rate_guess = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat
  executed_volume_fiat = trade_size_fiat / (1 + rate_guess)
  actual_rate = calculate_fee(executed_volume_fiat, is_maker=False) / executed_volume_fiat
  if actual_rate != rate_guess:
      executed_volume_fiat = trade_size_fiat / (1 + actual_rate)
  buy_fee = calculate_fee(executed_volume_fiat, is_maker=False)
  ```

## Verification Method
- **`api.py`**: Hardcode the `url` to a guaranteed `429` endpoint (or mock `requests.get` to yield a 429 response). Run `get_historical_ohlcv("XXBTZUSD")` and assert that the exception "Max retries exceeded" is raised instead of `UnboundLocalError`.
- **`backtest.py`**: Temporarily mock `calculate_fee()` to return a 0.40% rate for `< 50000` and `0.20%` for `>= 50000`. Run the backtest using a `trade_size_fiat` of exactly `50000`. Assert that `executed_volume_fiat + buy_fee == 50000.0`.
