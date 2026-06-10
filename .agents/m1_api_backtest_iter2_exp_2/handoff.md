# Investigation Report: Kraken API & Backtesting Bug Fixes

## 1. Observation
- **ZeroDivisionError**: In `backtest.py` at line 32, the code calculates `crypto_amount = (trade_size_fiat - buy_fee) / open_price` without verifying if `open_price` is zero or non-positive.
- **Negative Fees/Prices**: In `api.py` at line 25, `calculate_fee(trade_size, is_maker=False)` unconditionally multiplies `trade_size` by the fee rate, allowing negative outputs if `trade_size` is negative. In `backtest.py` at lines 24-25, negative prices are not filtered out.
- **Missing Balance Check**: In `backtest.py` at lines 27-44, the simulation loop repeatedly subtracts `trade_size_fiat` (default $100.0) from the user's `balance` (via `balance += trade_pnl` where `trade_pnl = net_return - trade_size_fiat`) but never checks if `balance >= trade_size_fiat` before the trade.
- **Rate Limits**: In `api.py` at lines 11-12, `requests.get(url)` is executed once and followed by `response.raise_for_status()`. There is no retry loop or exponential backoff mechanism for handling HTTP 429 status codes or JSON error responses containing rate limit indicators.
- **Fee Subtraction Flaw**: In `backtest.py` at lines 31-32, `buy_fee = calculate_fee(trade_size_fiat, is_maker=False)`. Here, `trade_size_fiat` represents the gross amount the user wants to spend. However, `calculate_fee` computes the fee as `gross_amount * fee_rate`. Kraken computes fees on the *executed volume*, meaning `gross_amount = executed_volume + fee` and `fee = executed_volume * fee_rate`. Thus, the current code slightly over-charges the fee.

## 2. Logic Chain
- By not validating `open_price` and `close_price`, bad historical data (e.g., zero or negative prices) will cause mathematical crashes or illogical negative outputs (Bug 1 & 2). 
- If `calculate_fee` lacks validation, upstream systems can pass negative volumes and extract funds (Bug 2). 
- Without an available balance check, the backtest allows buying power to exceed reality, invalidating the simulation (Bug 3).
- Since Kraken rate limits aggressively, standard `requests.get` calls will frequently fail and crash the pipeline unless wrapped in a retry mechanism with backoff (Bug 4).
- Mathematically, if a user spends $100 gross on a 0.4% fee, the executed volume $V$ satisfies $V \times 1.004 = \$100 \implies V \approx \$99.6016$, and the fee is $100 - V \approx \$0.3984$. The current logic computes $100 \times 0.004 = \$0.40$, leaving an executed volume of $99.60$. This inaccuracy compounds over multiple trades (Bug 5).

## 3. Caveats
- Kraken can signal rate limits via HTTP 429 status codes OR via HTTP 200 responses with `"EAPI:Rate limit exceeded"` in the JSON `error` array. The retry logic must handle both cases.
- The backtest logic skips trades with invalid prices rather than imputing data. This assumes skipping bad data points is acceptable.
- When `balance < trade_size_fiat`, the simplest fix is to `break` out of the simulation loop, assuming the simulation should end when funds are exhausted.

## 4. Conclusion
**Proposed Strategy for Implementer:**
1. **Fixing Bug 2 & 5 (`api.py`)**:
   - Update `calculate_fee` to raise a `ValueError` if the input amount is negative.
   - Add an optional boolean parameter `is_gross_amount=False` to `calculate_fee`. If true, compute the fee as `amount - (amount / (1 + fee_rate))`. Otherwise, return `amount * fee_rate` as before.
2. **Fixing Bug 4 (`api.py`)**:
   - Wrap the `requests.get` call in a `for attempt in range(max_retries):` loop.
   - Use `try/except requests.exceptions.RequestException` and inspect HTTP status code `429`. Also check `data.get('error')` for rate limit messages.
   - If rate-limited, use `time.sleep(base_delay * (2 ** attempt))` before retrying. Raise the exception if max retries are exceeded.
3. **Fixing Bug 1, 2, & 3 (`backtest.py`)**:
   - Inside the trade loop, verify if `balance < trade_size_fiat`. If so, `break` the loop.
   - Verify if `open_price <= 0` or `close_price <= 0`. If so, `continue` to the next trade (skip invalid data).
   - Update the `buy_fee` calculation to `calculate_fee(trade_size_fiat, is_maker=False, is_gross_amount=True)`. The `sell_fee` calculation is fine as-is because `sell_volume_fiat` is the executed volume (Bug 5 fixed).

## 5. Verification Method
- **Code Inspection**: Verify `api.py` and `backtest.py` have the appropriate conditional checks and math updates.
- **Tests**: The implementer should write or update tests checking negative fee rejections, rate limit retry behaviors, and zero/negative price handling.
- **Execution**: Run `python -m pytest` or `python scripts/run_backtest.py` locally and verify there are no crashes and math logic operates as expected.
