# Iteration 3 Synthesis

Based on Explorer 3's report, here is the concrete strategy to fix the remaining bugs identified by the Challengers and Auditor:

1. **ZeroDivisionError**: In `krakentrader/backtest.py`, add `if num_trades < 0: raise ValueError("num_trades must be >= 0")` at the start of `run_backtest`.
2. **Rate Limits**: In `krakentrader/api.py`, parse the JSON response *inside* the `requests.get` loop. If `response.status_code == 200`, check if the string `"Rate limit"` appears in any of the elements of `data.get('error', [])`. If it does, `time.sleep()` and `continue` to retry (using exponential backoff), just like for HTTP 429.
3. **CLI Arguments**: In `scripts/run_backtest.py`, add `argparse` to support `--data-dir`, `--coin`, and `--capital` (capital sets starting balance). If `--data-dir` is provided, load OHLCV data from `{data_dir}/{coin}_historical.csv` (CSV has open at index 1, close at index 4) instead of calling `get_historical_ohlcv`.
4. **Fee Tier Math**: In `krakentrader/backtest.py`, replace the hardcoded `calculate_fee(1.0)` call. Compute the effective rate dynamically:
   `effective_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat`
   `executed_volume_fiat = trade_size_fiat / (1 + effective_rate)`
   `buy_fee = calculate_fee(executed_volume_fiat, is_maker=False)`
