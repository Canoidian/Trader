# Handoff Report: Bug Investigation for Milestone 1 (Iteration 2)

## 1. Observation
- `krakentrader/backtest.py` lines 24-33 do not guard against `open_price <= 0` or `close_price <= 0`, leading to `ZeroDivisionError` when calculating `crypto_amount`, and allowing negative prices.
- `krakentrader/api.py` lines 25-31 calculate fees without validating that `trade_size` is non-negative.
- `krakentrader/backtest.py` lines 18-52 iterate through trades using `trade_size_fiat = 100.0` but never check if `balance >= trade_size_fiat`.
- `krakentrader/api.py` lines 10-14 call `requests.get()` and `raise_for_status()` without handling HTTP 429 (Too Many Requests) via retries.
- `krakentrader/backtest.py` lines 31-32 compute `buy_fee = calculate_fee(trade_size_fiat)` and subtract it from the gross `trade_size_fiat` to get `crypto_amount`. This charges the fee on the gross amount rather than the executed volume.

## 2. Logic Chain
- **Bug 1 & 2 (Negative/Zero Prices and ZeroDivisionError)**: Adding a guard clause `if open_price <= 0 or close_price <= 0: continue` in `backtest.py` prevents division by zero and invalid negative price calculations. Additionally, adding `if trade_size < 0: raise ValueError("trade_size cannot be negative")` in `api.py`'s `calculate_fee` solidifies the logic.
- **Bug 3 (Missing Balance Check)**: Checking `if balance < trade_size_fiat: break` before executing the buy side of the simulation ensures the balance doesn't drop below zero due to insufficient funds.
- **Bug 4 (Rate limits)**: Wrapping `requests.get` in a retry loop that intercepts `429` status codes and applies `time.sleep` with exponential backoff (e.g., 1s, 2s, 4s) addresses the rate-limit crashes.
- **Bug 5 (Fee Subtraction Flaw)**: The total cost $100 includes the fee. Thus, $100 = \text{Executed Volume} \times (1 + \text{fee\_rate})$. By querying the fee rate dynamically (`fee_rate = calculate_fee(1.0, is_maker=False)`), we can compute `executed_fiat = trade_size_fiat / (1 + fee_rate)`, then pass `executed_fiat` into `calculate_fee` and divide by `open_price`. This calculates fees based precisely on executed volume.

## 3. Caveats
- The backtest skips invalid data rows (where prices <= 0). This is acceptable for a simple backtester, but if data is extremely malformed, it could skip all trades.
- The 429 exponential backoff relies on `time.sleep`, making the process block synchronously. This is fine for a lightweight script but may need to be asynchronous in the future.

## 4. Conclusion
The Worker should apply the following fixes:
1. **`krakentrader/api.py`**:
   - In `calculate_fee`: `if trade_size < 0: raise ValueError(...)`
   - In `get_historical_ohlcv`: Wrap the HTTP request in a `for attempt in range(max_retries):` loop. Catch 429 errors and use `time.sleep` with exponential backoff.
2. **`krakentrader/backtest.py`**:
   - In `run_backtest`, add `if open_price <= 0 or close_price <= 0: continue` early in the loop.
   - Add `if balance < trade_size_fiat: break` before executing a trade.
   - Refactor the buy logic:
     ```python
     fee_rate = calculate_fee(1.0, is_maker=False)
     executed_fiat = trade_size_fiat / (1 + fee_rate)
     buy_fee = calculate_fee(executed_fiat, is_maker=False)
     crypto_amount = executed_fiat / open_price
     ```

## 5. Verification Method
- **Static**: Review the code for logic implementation.
- **Validation**: Verify that `$100` gross spend exactly equals `buy_fee + executed_fiat` and that `buy_fee == executed_fiat * 0.0040`. Verify no ZeroDivisionError occurs when mocking `open_price = 0`. Verify 429 errors are retried.
