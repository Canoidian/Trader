import time
import logging
import random
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'state.json')

from krakentrader.api import get_balance, create_order, get_historical_ohlcv, get_tradable_pairs, get_ticker
from krakentrader.analysis import calculate_composite_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TRADE_FRACTION = 0.95    
MIN_TRADE_AMOUNT_USD = 5.0 
MAX_CONCURRENT_TRADES = 3
TRAILING_STOP_PCT = 0.03 # 3.0% trailing stop loss
MAX_HOLD_HOURS = 6.0     # Maximum hours to hold a trade
POLL_INTERVAL = 30       

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                if isinstance(state, list):
                    logging.info(f"Recovered {len(state)} open positions from disk.")
                    return state
        except Exception as e:
            logging.error(f"Failed to load state: {e}")
    return []

def save_state(state):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logging.error(f"Failed to save state: {e}")

def get_usd_value(asset, amount):
    if amount <= 0:
        return 0.0
    if 'USD' in asset:
        return amount
    try:
        pair = asset + 'ZUSD' if not asset.endswith('USD') else asset
        price = get_ticker(pair)
        if price:
            return amount * price
    except:
        pass
    return 0.0

def consolidate_fiat(balances):
    # Automatically convert Euro dust to USD if it meets Kraken's 4 EUR minimum
    eur_balance = float(balances.get('ZEUR', balances.get('EUR', 0.0)))
    if eur_balance >= 4.0:
        logging.info(f"Auto-Consolidating {eur_balance:.2f} EUR into USD...")
        try:
            res = create_order('ZEURZUSD', 'sell', 'market', eur_balance)
            logging.info(f"Consolidation Success: {res}")
            return True
        except Exception as e:
            logging.error(f"Failed to consolidate EUR: {e}")
    return False

def run_loop():
    logging.info("Starting Multi-Asset Portfolio Trading Loop...")
    open_positions = load_state()  
    
    while True:
        try:
            # STEP 1: MONITOR & SELL
            current_time = time.time()
            for pos in list(open_positions):
                pair = pos['pair']
                buy_price = pos['buy_price']
                volume = pos['volume']
                
                # Load or initialize dynamic state
                buy_time = pos.get('buy_time', current_time)
                highest_price_seen = pos.get('highest_price_seen', buy_price)
                
                try:
                    current_price = get_ticker(pair)
                    
                    # Update highest price seen
                    if current_price > highest_price_seen:
                        highest_price_seen = current_price
                        pos['highest_price_seen'] = highest_price_seen
                        save_state(open_positions)
                        
                    trailing_stop = highest_price_seen * (1 - TRAILING_STOP_PCT)
                    hold_time_hours = (current_time - buy_time) / 3600.0
                    
                    logging.info(f"[MONITOR] {pair}: Current ${current_price:.6f} | High ${highest_price_seen:.6f} | Stop ${trailing_stop:.6f} | Held {hold_time_hours:.1f}h")
                    
                    if current_price <= trailing_stop:
                        logging.info(f"[SELL] TRAILING STOP HIT! Selling {volume:.6f} {pair} at ${current_price:.6f}")
                        create_order(pair, 'sell', 'market', volume)
                        open_positions.remove(pos)
                        save_state(open_positions)
                    elif hold_time_hours >= MAX_HOLD_HOURS:
                        logging.info(f"[SELL] STALE TRADE CUT! Selling {volume:.6f} {pair} after {hold_time_hours:.1f} hours at ${current_price:.6f}")
                        create_order(pair, 'sell', 'market', volume)
                        open_positions.remove(pos)
                        save_state(open_positions)
                except Exception as e:
                    logging.error(f"Error checking {pair}: {e}")

            # STEP 2: CHECK BALANCES (What crypto/USD do we own?)
            if len(open_positions) < MAX_CONCURRENT_TRADES:
                try:
                    balances = get_balance()
                except Exception as e:
                    logging.error(f"Failed to fetch balances (Check API keys!): {e}")
                    balances = {}
                    
                usable_assets = []
                for asset, amount_str in balances.items():
                    amount = float(amount_str)
                    usd_val = get_usd_value(asset, amount)
                    if usd_val >= MIN_TRADE_AMOUNT_USD:
                        usable_assets.append({'asset': asset, 'amount': amount, 'usd_val': usd_val})
                        
                if not usable_assets:
                    logging.info("No usable assets found (wallet is empty or balances < $5). Attempting auto-consolidation...")
                    if consolidate_fiat(balances):
                        time.sleep(5)  # Let balances settle on Kraken's servers
                        continue       # Restart loop to fetch new USD balance
                    else:
                        logging.info("Consolidation not possible or failed. Waiting...")
                
                # STEP 3: MARKET RESEARCH
                if usable_assets:
                    quote_currencies = [a['asset'] for a in usable_assets]
                    tradable_pairs_dict = get_tradable_pairs(quote_currencies)
                    all_pairs = list(tradable_pairs_dict.keys())
                    if all_pairs:
                        sample_pairs = random.sample(all_pairs, min(10, len(all_pairs)))
                        
                        best_pair = None
                        best_score = -9999
                        best_price = 0
                        best_quote_asset = None
                        
                        for pair in sample_pairs:
                            try:
                                ohlcv = get_historical_ohlcv(pair)
                                if not ohlcv or len(ohlcv) < 15: continue
                                closes = [float(row[4]) for row in ohlcv]
                                score = calculate_composite_score(closes)
                                if score > best_score:
                                    best_score = score
                                    best_pair = pair
                                    best_price = closes[-1]
                                    best_quote_asset = tradable_pairs_dict[pair]
                            except:
                                pass
                                
                        if best_score > 10 and best_quote_asset:
                            # STEP 4: BUY
                            asset_info = next(a for a in usable_assets if a['asset'] == best_quote_asset)
                            trade_amount = asset_info['amount'] * TRADE_FRACTION
                            volume = trade_amount / best_price
                            
                            logging.info(f"[BUY] Score {best_score:.2f}. Using {trade_amount:.6f} {best_quote_asset} to buy {best_pair}")
                            try:
                                create_order(best_pair, 'buy', 'market', volume)
                                open_positions.append({
                                    'pair': best_pair,
                                    'buy_price': best_price,
                                    'volume': volume,
                                    'quote_asset': best_quote_asset,
                                    'buy_time': time.time(),
                                    'highest_price_seen': best_price
                                })
                                save_state(open_positions)
                            except Exception as e:
                                logging.error(f"Failed buy order: {e}")
            else:
                logging.info(f"Max positions ({MAX_CONCURRENT_TRADES}) reached. Waiting for sells.")
                
            time.sleep(POLL_INTERVAL)
                    
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_loop()
