import sys
import os

import argparse
import csv

# Add parent directory to path to allow importing krakentrader
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from krakentrader.api import get_historical_ohlcv
from krakentrader.backtest import run_backtest

def main():
    parser = argparse.ArgumentParser(description="Run backtest for KrakenTrader")
    parser.add_argument("--data-dir", type=str, help="Directory containing historical CSV data")
    parser.add_argument("--coin", type=str, default="BTC", help="Coin pair to backtest")
    parser.add_argument("--capital", type=float, default=1000.0, help="Starting capital")
    args = parser.parse_args()

    if args.capital <= 0:
        print("Error: Starting capital must be > 0.")
        sys.exit(1)

    pair = args.coin.strip() if args.coin else "BTC"
    if not pair:
        pair = "BTC"
    print(f"Fetching historical OHLCV data for {pair}...")
    
    data = []
    if args.data_dir:
        csv_path = os.path.join(args.data_dir, f"{pair}_historical.csv")
        try:
            with open(csv_path, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    data.append(row)
        except Exception as e:
            print(f"Failed to load CSV data: {e}")
            sys.exit(1)
    else:
        try:
            data = get_historical_ohlcv(pair)
        except Exception as e:
            print(f"Failed to fetch data: {e}")
            sys.exit(1)

    if not data:
        print("No data returned.")
        sys.exit(1)
        
    print(f"Fetched {len(data)} data points.")
    print("Running backtest simulating 10 trades...")
    
    result = run_backtest(data, initial_balance=args.capital, num_trades=10)
    
    print("\n--- Trade Log ---")
    for t in result['trades']:
        print(f"Trade #{t['trade_index']:02d}: Open: ${t['open_price']:.2f}, Close: ${t['close_price']:.2f} "
              f"| Buy Fee: ${t['buy_fee']:.4f}, Sell Fee: ${t['sell_fee']:.4f} | Net PnL: ${t['trade_pnl']:.4f}")
              
    print("\n--- Final Results ---")
    num_trades = len(result['trades'])
    if num_trades == 0:
        print("0 trades executed (no valid trade opportunities found in data)")
    else:
        print(f"Total Trades Executed: {num_trades}")
    print(f"Cumulative PnL: ${result['cumulative_pnl']:.4f}")
    print(f"Final Balance: ${result['final_balance']:.4f}")

if __name__ == "__main__":
    main()
