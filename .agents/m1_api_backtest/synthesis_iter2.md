# Iteration 2 Synthesis

Based on Explorer 1's report, here is the concrete strategy to fix the bugs identified by the Challengers:

**krakentrader/api.py**:
1. Update `calculate_fee(trade_size, is_maker=False)` to check `if trade_size < 0:` and raise a `ValueError`.
2. Update `get_historical_ohlcv(pair)` to implement an exponential backoff retry loop (e.g. 3 retries, `time.sleep(1 * (2 ** attempt))`) specifically catching HTTP 429 status codes before calling `response.raise_for_status()`.

**krakentrader/backtest.py**:
1. Balance check: At the start of the `for` loop, limit the trade size based on the current balance:
   `trade_size_fiat = min(100.0, balance)`
   `if trade_size_fiat <= 0: break`
2. Price validation: Skip iteration if prices are invalid:
   `if open_price <= 0 or close_price <= 0: continue`
3. Fee subtraction flaw: Fix the fee math by calculating the exact fee on the executed volume rather than subtracting from the gross.
   `fee_rate = calculate_fee(1.0, is_maker=False)`
   `executed_volume_fiat = trade_size_fiat / (1 + fee_rate)`
   `buy_fee = calculate_fee(executed_volume_fiat, is_maker=False)`
   `crypto_amount = executed_volume_fiat / open_price`
   Ensure sell side is also mathematically correct (deducting fee from proceeds).
