from krakentrader.api import calculate_fee

def run_backtest(ohlcv_data, initial_balance=1000.0, num_trades=10):
    """
    Run a simple backtest on the provided OHLCV data.
    Simulates round-trip trades (buy at open, sell at close) over the historical data.
    """
    if num_trades < 0:
        raise ValueError("num_trades must be >= 0")
    balance = initial_balance
    trades = []
    
    # Determine the step size to spread the trades out evenly over the available data
    step = len(ohlcv_data) // (num_trades + 1)
    if step == 0:
        step = 1
        
    cumulative_pnl = 0.0
    
    for i in range(num_trades):
        idx = (i + 1) * step
        if idx >= len(ohlcv_data):
            break
            
        row = ohlcv_data[idx]
        open_price = float(row[1])
        close_price = float(row[4])
        
        if open_price <= 0 or close_price <= 0:
            continue
        
        # Skip zero-variance candles (open == close) — no price movement, fees only
        if open_price == close_price:
            continue
        
        # We simulate trading $100 per trade
        trade_size_fiat = min(100.0, balance)
        if trade_size_fiat <= 0:
            break
        
        # Simulate BUY at open price
        # First pass estimate
        est_rate = calculate_fee(trade_size_fiat, is_maker=False) / trade_size_fiat
        est_vol = trade_size_fiat / (1 + est_rate)
        
        # Second pass exact
        exact_rate = calculate_fee(est_vol, is_maker=False) / est_vol
        executed_volume_fiat = trade_size_fiat / (1 + exact_rate)
        buy_fee = calculate_fee(executed_volume_fiat, is_maker=False)
        crypto_amount = executed_volume_fiat / open_price
        
        # Simulate SELL at close price
        sell_volume_fiat = crypto_amount * close_price
        sell_fee = calculate_fee(sell_volume_fiat, is_maker=False)
        net_return = sell_volume_fiat - sell_fee
        
        # Calculate PnL for this specific trade
        trade_pnl = net_return - trade_size_fiat
        
        cumulative_pnl += trade_pnl
        balance += trade_pnl
        
        trades.append({
            'trade_index': i + 1,
            'open_price': open_price,
            'close_price': close_price,
            'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'trade_pnl': trade_pnl
        })
        
    return {
        'trades': trades,
        'final_balance': balance,
        'cumulative_pnl': cumulative_pnl
    }
