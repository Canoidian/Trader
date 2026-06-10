# Handoff Report: Review of Milestone 1 (Iteration 3)

## 1. Observation
- In `krakentrader/api.py`, `get_historical_ohlcv` implements a 3-retry loop for `requests.get`. If `response.status_code == 429`, it skips assignment and continues:
  ```python
  if response.status_code == 429:
      time.sleep(1 * (2 ** attempt))
      continue
  ```
- If all three attempts return a 429 status code, the loop exits and hits line 28: `if data.get('error'):`. However, `data` was never initialized.
- In `krakentrader/backtest.py`, the fee tier math was updated to use the full budget (`trade_size_fiat`) to calculate the effective fee rate:
  ```python
  effective_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat
  ```

## 2. Logic Chain
- Because `data` is only assigned via `data = response.json()` when a request does not result in an HTTP 429 status code, failing three times with HTTP 429 leaves `data` completely unassigned in the local scope.
- Evaluating `data.get('error')` on an unassigned variable raises an `UnboundLocalError`, causing an unhandled crash rather than gracefully raising the expected rate-limit or API exception.
- For the fee tier logic: Using `trade_size_fiat` (budget) to compute the tier rate is slightly inaccurate. The executable volume is strictly less than the budget. If a budget lies slightly above a tier threshold (e.g., $100.00), it will fetch the lower tier rate, while the actual traded volume (e.g., $99.60) should fall into a higher fee tier.

## 3. Caveats
- I could not run the test suite locally due to execution environment constraints (run_command timeout), but the logic flaws are evident through static analysis.

## 4. Conclusion
- The fix for the Rate Limits JSON response is implemented but introduces a fatal `UnboundLocalError` when handling actual HTTP 429 status codes under sustained rate limiting.
- The Future-Proofing Fee Tier Math issue is improved but still technically flawed at tier boundaries due to the assumption that budget determines the tier rather than actual volume.
- **Verdict**: REQUEST_CHANGES.

## 5. Verification Method
- **Bug 1**: Mock `requests.get` to always return a response object with `status_code=429` and execute `get_historical_ohlcv("XXBTZUSD")`. Observe the `UnboundLocalError`.
- **Bug 2**: Perform boundary testing with mock tier rates in `calculate_fee` to observe over-calculation of crypto amounts when the budget crosses a threshold but actual volume does not.
