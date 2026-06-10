import sys
import os
import json
import urllib.request
import time
import argparse
import csv

# Ensure krakentrader can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from krakentrader.analysis import calculate_composite_score, calculate_rsi, calculate_sma, calculate_volatility

def fetch_data(pair):
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('error'):
                print(f"Error fetching {pair}: {data['error']}")
                return None
            
            keys = [k for k in data['result'].keys() if k != 'last']
            if not keys:
                return None
            
            ohlc_data = data['result'][keys[0]]
            # OHLC format: [time, open, high, low, close, vwap, volume, count]
            closes = [float(candle[4]) for candle in ohlc_data]
            return closes
    except Exception as e:
        print(f"Failed to fetch {pair}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Run analysis for KrakenTrader")
    parser.add_argument("--data-dir", type=str, help="Directory containing historical CSV data")
    parser.add_argument("--coins", type=str, default="XXBTZUSD,XETHZUSD,SOLUSD", help="Comma-separated list of coins to analyze")
    args = parser.parse_args()

    pairs = [p.strip() for p in args.coins.split(',') if p.strip()]
    if len(pairs) < 3:
        print("Error: At least 3 coins must be provided for analysis.")
        sys.exit(1)
        
    results = []
    
    print("Fetching data and running analysis...")
    for pair in pairs:
        print(f"Fetching {pair}...")
        
        closes = None
        if args.data_dir:
            csv_path = os.path.join(args.data_dir, f"{pair}_historical.csv")
            try:
                with open(csv_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    closes = []
                    for row in reader:
                        if len(row) > 4:
                            try:
                                closes.append(float(row[4]))
                            except ValueError:
                                pass
            except Exception as e:
                print(f"Failed to load CSV data for {pair}: {e}")
                sys.exit(1)
        else:
            closes = fetch_data(pair)
            if closes is None:
                print(f"Failed to fetch live data for {pair}")
                sys.exit(1)
            
        if closes and len(closes) >= 15:
            score = calculate_composite_score(closes)
            rsi = calculate_rsi(closes, 14)
            sma = calculate_sma(closes, 14)
            vol = calculate_volatility(closes)
            
            results.append({
                'pair': pair,
                'score': score,
                'rsi': rsi if rsi is not None else 0,
                'sma': sma if sma is not None else 0,
                'volatility': vol,
                'last_price': closes[-1]
            })
        else:
            print(f"Not enough data for {pair}")
            
        if not args.data_dir:
            time.sleep(1) # Rate limit avoidance
        
    if not results:
        print("No results to display (insufficient data for all coins).")
        sys.exit(0)
        
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n--- Ranked Analysis ---")
    print(f"{'Pair':<12} | {'Score':<8} | {'Price':<10} | {'RSI':<6} | {'SMA(14)':<10} | {'Vol':<6}")
    print("-" * 65)
    for res in results:
        print(f"{res['pair']:<12} | {res['score']:<8.2f} | {res['last_price']:<10.2f} | {res['rsi']:<6.2f} | {res['sma']:<10.2f} | {res['volatility']:<6.4f}")
        
if __name__ == '__main__':
    main()
