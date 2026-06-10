# Iteration 4 Synthesis

Based on Explorer 3's analysis, apply the following fixes:

1. **UnboundLocalError in `api.py`**:
   In `krakentrader/api.py`, within `get_historical_ohlcv`, there is a `for attempt in range(3):` loop with an `else:` block containing `pass`. If all 3 attempts hit HTTP 429, the loop falls through to `else: pass` and then tries to access `data`, causing an `UnboundLocalError`.
   **Fix**: Change `pass` to `raise Exception("Kraken API rate limit exceeded after 3 attempts.")` inside the `else:` block.

2. **Fee Tier Edge Case in `backtest.py`**:
   In `krakentrader/backtest.py`, calculating `effective_rate` using `trade_size_fiat` causes an edge case at fee tier boundaries, because the actual `executed_volume_fiat` is slightly less than `trade_size_fiat`.
   **Fix**: Replace the current `effective_rate` logic with a two-pass estimation:
   ```python
   # First pass estimate
   est_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat
   est_vol = trade_size_fiat / (1 + est_rate)
   
   # Second pass exact
   exact_rate = calculate_fee(est_vol, is_maker=False) / est_vol
   executed_volume_fiat = trade_size_fiat / (1 + exact_rate)
   buy_fee = calculate_fee(executed_volume_fiat, is_maker=False)
   ```
