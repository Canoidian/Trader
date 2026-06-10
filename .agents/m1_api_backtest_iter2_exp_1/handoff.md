# Handoff Report: Milestone 1 API & Backtest Bug Fixes (Iteration 2)

## 1. Observation
- **ZeroDivisionError**: `krakentrader/backtest.py:32` has `crypto_amount = (trade_size_fiat - buy_fee) / open_price`. If `open_price` is 0, this raises a `ZeroDivisionError`.
- **Negative Fees/Prices**: `krakentrader/api.py:31` computes `trade_size * fee_rate` without validating if `trade_size` is non-negative. Additionally, `krakentrader/backtest.py:24` parses `open_price` and `close_price` without bounds checking, which could lead to negative prices.
- **Missing Balance Check**: `krakentrader/backtest.py:43` updates `balance += trade_pnl` but never validates if `balance >= trade_size_fiat` prior to a trade, allowing negative balances.
- **Rate Limit (429)**: `krakentrader/api.py:11` calls `requests.get(url)` and immediately calls `response.raise_for_status()`, lacking retry logic or backoff for HTTP 429 statuses.
- **Fee Subtraction Flaw**: `krakentrader/backtest.py:31-32` calculates `buy_fee = calculate_fee(trade_size_fiat)` and subtracts it from `trade_size_fiat`. However, Kraken applies fees to the *executed volume*, meaning `trade_size_fiat = executed_volume + fee`.

## 2. Logic Chain
1. To prevent `ZeroDivisionError` and negative math issues, we must filter out invalid OHLCV rows in `run_backtest` (e.g., skip iteration if `open_price <= 0` or `close_price <= 0`).
2. To strictly prevent negative fees, `calculate_fee` should explicitly enforce `trade_size >= 0` via a `ValueError`.
3. To enforce balance bounds, the backtest loop must evaluate `if balance < trade_size_fiat:` and either limit `trade_size_fiat` to `balance` or break the loop if trading is impossible. 
4. To handle 429 rate limits, a `requests.Session` with `urllib3.util.Retry` can be used, or a manual loop using `time.sleep` with exponential backoff on `status_code == 429`. A manual loop is simpler to implement correctly with `requests`.
5. To fix the fee subtraction logic without altering the `calculate_fee` signature, we can dynamically retrieve the `fee_rate` by calling `calculate_fee(1.0, is_maker=False)`, compute `executed_volume = trade_size_fiat / (1 + fee_rate)`, and then calculate `buy_fee = calculate_fee(executed_volume, is_maker=False)`.

## 3. Caveats
- I assumed that if `balance < 100.0`, the system should scale down the `trade_size_fiat` to the remaining balance. If `balance <= 0`, it should break the loop. This is standard backtesting behavior.
- I assumed a maximum of 3 to 5 retries for the rate limit backoff is appropriate.
- I did not modify tests since none were provided or required in my scope.

## 4. Conclusion
The Implementer agent should apply the following fixes:

**krakentrader/api.py**:
1. Update `calculate_fee(trade_size, is_maker=False)` to check `if trade_size < 0:` and raise a `ValueError`.
2. Update `get_historical_ohlcv(pair)` to implement a retry loop catching HTTP 429. E.g.:
```python
import time
max_retries = 3
for attempt in range(max_retries):
    response = requests.get(url)
    if response.status_code == 429:
        time.sleep(1 * (2 ** attempt))
        continue
    response.raise_for_status()
    break
```

**krakentrader/backtest.py**:
1. At the start of the `for` loop, limit the trade size based on the current balance:
```python
trade_size_fiat = min(100.0, balance)
if trade_size_fiat <= 0:
    break
```
2. Check for invalid prices:
```python
if open_price <= 0 or close_price <= 0:
    continue
```
3. Fix the fee math by deriving the fee rate:
```python
fee_rate = calculate_fee(1.0, is_maker=False)
executed_volume_fiat = trade_size_fiat / (1 + fee_rate)
buy_fee = calculate_fee(executed_volume_fiat, is_maker=False)
crypto_amount = executed_volume_fiat / open_price
```

## 5. Verification Method
- **Static Analysis**: View the updated `krakentrader/api.py` and `krakentrader/backtest.py` to confirm the code matches the logic above.
- **Unit Testing**: Run `python -m pytest` or `python scripts/run_backtest.py` (if available) with a simulated `open_price=0` to ensure no `ZeroDivisionError` is raised. Verify the final `trade_pnl` calculates accurately.
