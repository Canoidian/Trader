import time
import logging
import random
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'state.json')

import krakentrader.api as _kraken_api
from krakentrader.api import (
    get_balance, create_order, get_historical_ohlcv,
    get_historical_ohlcv_interval, get_tradable_pairs, get_ticker
)
from krakentrader.analysis import calculate_composite_score
from krakentrader.regime import get_market_regime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MIN_TRADE_AMOUNT_USD = 5.0
MAX_CONCURRENT_TRADES = 3
TRAILING_STOP_PCT = 0.03
MAX_HOLD_HOURS = 6.0
POLL_INTERVAL = 30
SAMPLE_PAIRS = 30

def confidence_to_fraction(score: float) -> float:
    if score >= 90:
        return 0.95
    if score >= 80:
        return 0.80
    if score >= 70:
        return 0.65
    return 0.40

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
    
    if not os.path.exists(os.path.join(os.path.dirname(STATE_FILE), 'model.pkl')):
        logging.warning("No ML model (model.pkl) found! The bot will use the naive fallback algorithm which is very conservative and may not buy anything. Run krakentrader/ml_trainer.py to train the AI!")
        
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
                    regime, buy_threshold = get_market_regime(_kraken_api)

                    quote_currencies = [a['asset'] for a in usable_assets]
                    tradable_pairs_dict = get_tradable_pairs(quote_currencies)
                    all_pairs = list(tradable_pairs_dict.keys())

                    if all_pairs:
                        sample_pairs = random.sample(all_pairs, min(SAMPLE_PAIRS, len(all_pairs)))

                        best_pair = None
                        best_score = -9999
                        best_price = 0
                        best_quote_asset = None

                        for pair in sample_pairs:
                            try:
                                ohlcv = get_historical_ohlcv(pair)
                                if not ohlcv or len(ohlcv) < 35:
                                    continue
                                closes = [float(row[4]) for row in ohlcv]
                                highs = [float(row[2]) for row in ohlcv]
                                lows = [float(row[3]) for row in ohlcv]
                                volumes = [float(row[6]) for row in ohlcv]
                                vwaps = [float(row[5]) for row in ohlcv]

                                closes_5m, closes_15m = None, None
                                try:
                                    ohlcv_5m = get_historical_ohlcv_interval(pair, 5)
                                    closes_5m = [float(r[4]) for r in ohlcv_5m] if ohlcv_5m else None
                                except Exception:
                                    pass
                                try:
                                    ohlcv_15m = get_historical_ohlcv_interval(pair, 15)
                                    closes_15m = [float(r[4]) for r in ohlcv_15m] if ohlcv_15m else None
                                except Exception:
                                    pass

                                score = calculate_composite_score(
                                    closes, highs=highs, lows=lows,
                                    volumes=volumes, vwaps=vwaps,
                                    closes_5m=closes_5m, closes_15m=closes_15m
                                )
                                if score > best_score:
                                    best_score = score
                                    best_pair = pair
                                    best_price = closes[-1]
                                    best_quote_asset = tradable_pairs_dict[pair]

                                time.sleep(0.05)
                            except Exception:
                                pass

                        if best_score > buy_threshold and best_quote_asset:
                            # STEP 4: BUY
                            asset_info = next(a for a in usable_assets if a['asset'] == best_quote_asset)
                            trade_fraction = confidence_to_fraction(best_score)
                            trade_amount = asset_info['amount'] * trade_fraction
                            volume = trade_amount / best_price

                            logging.info(f"[BUY] {regime} regime | Score {best_score:.1f}% | Threshold {buy_threshold}% | Sizing {trade_fraction*100:.0f}% | Using {trade_amount:.6f} {best_quote_asset} to buy {best_pair}")
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
