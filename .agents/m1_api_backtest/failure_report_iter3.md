# Iteration 3 Failure Report

Reviewer 1 (Iteration 3) vetoed the implementation with the following critical findings:

1. **[Critical] UnboundLocalError on Consecutive HTTP 429 Responses**
   - **Where**: `krakentrader/api.py`, `get_historical_ohlcv()`.
   - **What**: If the Kraken API returns HTTP 429 for all three attempts, the loop exits without `data` ever being assigned. When the code later checks `if data.get('error'):`, it throws a fatal `UnboundLocalError`.

2. **[Major] Fee Tier Threshold Edge Case**
   - **Where**: `krakentrader/backtest.py`, calculating `effective_rate`.
   - **What**: The effective fee rate is currently determined using the total fiat budget (`trade_size_fiat`). This is mathematically flawed at tier boundaries. If the total budget exactly meets a lower-fee tier (e.g., $50,000), the calculated fee rate will use that tier. However, because fees are subtracted from the fiat amount *before* buying, the actual executed volume might be $49,900, which falls into a *higher-fee* tier. This discrepancy causes the backtest to over-calculate the crypto amount and misrepresent the actual fees Kraken would charge on the order.

Please investigate these new issues and propose a fix.
