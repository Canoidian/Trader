import requests
import time
import urllib.parse
import hashlib
import hmac
import base64
import os
from dotenv import load_dotenv

load_dotenv()

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

def get_tradable_pairs(quote_currencies):
    url = "https://api.kraken.com/0/public/AssetPairs"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data.get('error'):
        raise Exception(f"Kraken API error: {data['error']}")
    
    pairs = {}
    for pair_name, info in data['result'].items():
        quote_asset = info.get('quote')
        if quote_asset in quote_currencies:
            pairs[pair_name] = quote_asset
    return pairs

def get_ticker(pair):
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data.get('error'):
        raise Exception(f"Kraken API error: {data['error']}")
        
    for key, info in data['result'].items():
        return float(info['c'][0])
    return None

def calculate_fee(trade_size, is_maker=False):
    """
    Calculate explicit fee for the given trade_size.
    Kraken base tier: 0.25% maker, 0.40% taker.
    """
    if trade_size < 0:
        raise ValueError("Trade size cannot be negative")
    fee_rate = 0.0025 if is_maker else 0.0040
    return trade_size * fee_rate

def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def private_request(endpoint, data=None):
    if data is None:
        data = {}
        
    api_key = os.getenv("KRAKEN_API_KEY")
    api_secret = os.getenv("KRAKEN_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("KRAKEN_API_KEY and KRAKEN_API_SECRET must be set in .env")
        
    urlpath = f'/0/private/{endpoint}'
    url = f'https://api.kraken.com{urlpath}'
    
    data['nonce'] = str(int(1000 * time.time()))
    headers = {
        'API-Key': api_key,
        'API-Sign': get_kraken_signature(urlpath, data, api_secret)
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    res_data = response.json()
    if res_data.get('error'):
        raise Exception(f"Kraken private API error: {res_data['error']}")
    return res_data.get('result', {})

def get_balance():
    return private_request('Balance')

def create_order(pair, type, ordertype, volume, price=None):
    data = {
        'pair': pair,
        'type': type,  # 'buy' or 'sell'
        'ordertype': ordertype, # 'market' or 'limit'
        'volume': str(volume)
    }
    if price is not None:
        data['price'] = str(price)
    return private_request('AddOrder', data)
