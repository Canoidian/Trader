## Consensus
- Both Explorer 2 and 3 agree that `requests` is sufficient and preferable to `ccxt` for fetching Kraken's public OHLC API.
- Historical data should be fetched from `https://api.kraken.com/0/public/OHLC`.
- Fee calculation should be implemented in `calculate_fee(trade_size, is_maker=False)` using Kraken's base tier (0.25% maker, 0.40% taker) and hardcoded logic.
- Code layout needs to be created from scratch: `krakentrader/api.py`, `krakentrader/backtest.py`, and `scripts/run_backtest.py`.

## Actionable Instructions for Worker
1. Create `requirements.txt` containing `requests`.
2. Create `krakentrader/__init__.py`.
3. Create `krakentrader/api.py`:
   - Implement `get_historical_ohlcv(pair)` using `requests` to fetch from Kraken OHLC endpoint.
   - Implement `calculate_fee(trade_size, is_maker=False)` explicitly computing the fee amount.
4. Create `krakentrader/backtest.py`:
   - Implement a backtesting loop that evaluates at least 10 trades over the historical OHLC data.
   - For each trade, explicitly call `calculate_fee` and subtract the fee from the PnL.
5. Create `scripts/run_backtest.py`:
   - Serve as the CLI entry point.
   - Run the simulation, outputting evidence of at least 10 simulated trades.
   - Log explicit fee deductions for each trade.
   - Output the final PnL summary proving the fee calculation works.
