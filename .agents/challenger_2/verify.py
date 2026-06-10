import json

def verify_math():
    ohlcv_data = [
        [1, 100.0, 110.0, 90.0, 200.0, 0, 0, 0] # Open = 100, Close = 200
    ]
    
    # Simulating the exact math in backtest.py
    trade_size_fiat = 100.0
    open_price = 100.0
    close_price = 200.0
    
    # The backtester logic:
    buy_fee_deducted = 100.0 * 0.004 # 0.40
    crypto_amount = (trade_size_fiat - buy_fee_deducted) / open_price # 99.6 / 100 = 0.996
    
    # Proof of flaw:
    # If the executed fiat volume is 99.6, the true Kraken fee on that volume should be:
    true_buy_fee = (crypto_amount * open_price) * 0.004 # 99.6 * 0.004 = 0.3984
    
    # The backtester over-deducted the fee by:
    fee_error = buy_fee_deducted - true_buy_fee # 0.40 - 0.3984 = 0.0016
    
    # Sell side
    sell_volume_fiat = crypto_amount * close_price # 0.996 * 200 = 199.2
    sell_fee = sell_volume_fiat * 0.004 # 0.7968
    net_return = sell_volume_fiat - sell_fee # 199.2 - 0.7968 = 198.4032
    
    trade_pnl = net_return - trade_size_fiat # 198.4032 - 100 = 98.4032
    
    report = {
        "executed_buy_volume": crypto_amount * open_price,
        "fee_deducted_by_backtester": buy_fee_deducted,
        "true_fee_for_executed_volume": true_buy_fee,
        "fee_error": fee_error
    }
    
    print(json.dumps(report, indent=2))
    
    return report

if __name__ == '__main__':
    verify_math()
