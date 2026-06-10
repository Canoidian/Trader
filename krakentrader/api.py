import requests
import time

def get_historical_ohlcv(pair):
    """
    Fetch historical OHLC data from Kraken for the given pair.
    Returns a list of OHLCV data.
    Each row in the result typically contains:
    [time, open, high, low, close, vwap, volume, count]
    """
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}"
    
    for attempt in range(3):
        response = requests.get(url)
        if response.status_code == 429:
            time.sleep(1 * (2 ** attempt))
            continue
        response.raise_for_status()
        data = response.json()
        if any("Rate limit" in str(err) for err in data.get('error', [])):
            time.sleep(1 * (2 ** attempt))
            continue
        break
    else:
        raise Exception("Kraken API rate limit exceeded after 3 attempts.")

    
    if data.get('error'):
        raise Exception(f"Kraken API error: {data['error']}")
        
    # The result contains the pair name (which might differ from the requested string) and 'last'
    for key in data['result'].keys():
        if key != 'last':
            return data['result'][key]
            
    return []

def calculate_fee(trade_size, is_maker=False):
    """
    Calculate explicit fee for the given trade_size.
    Kraken base tier: 0.25% maker, 0.40% taker.
    """
    if trade_size < 0:
        raise ValueError("Trade size cannot be negative")
    fee_rate = 0.0025 if is_maker else 0.0040
    return trade_size * fee_rate
