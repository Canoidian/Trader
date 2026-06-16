import math
import logging
import statistics
import os
try:
    import joblib
except ImportError:
    pass

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'model.pkl')
_model_cache = None

def load_model():
    global _model_cache
    if _model_cache is None and os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
        except Exception as e:
            logging.warning(f"Failed to load model: {e}")
    return _model_cache

def calculate_sma(closes, period):
    if period <= 0:
        return None
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period

def calculate_rsi(closes, period=14):
    if period <= 0:
        return None
    if len(closes) <= period:
        return None
    
    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
            
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(closes) - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0:
        if avg_gain == 0:
            return 50.0
        return 100.0
        
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calculate_volatility(closes):
    if len(closes) < 2:
        return 0.0
    returns = []
    for i in range(1, len(closes)):
        if closes[i-1] == 0:
            returns.append(0.0)
        else:
            returns.append((closes[i] - closes[i-1]) / closes[i-1])
    if len(returns) < 2:
        return 0.0
    return statistics.stdev(returns)

def calculate_ema(closes, period):
    if period <= 0 or len(closes) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calculate_macd(closes):
    if len(closes) < 35:
        return None, None, None
    k12 = 2.0 / 13
    k26 = 2.0 / 27
    k9 = 2.0 / 10
    ema12 = sum(closes[:12]) / 12
    ema26 = sum(closes[:26]) / 26
    for price in closes[12:26]:
        ema12 = price * k12 + ema12 * (1 - k12)
    macd_series = []
    for price in closes[26:]:
        ema12 = price * k12 + ema12 * (1 - k12)
        ema26 = price * k26 + ema26 * (1 - k26)
        macd_series.append(ema12 - ema26)
    if len(macd_series) < 9:
        return None, None, None
    signal = sum(macd_series[:9]) / 9
    for m in macd_series[9:]:
        signal = m * k9 + signal * (1 - k9)
    macd_line = macd_series[-1]
    return macd_line, signal, macd_line - signal

def calculate_bollinger_bands(closes, period=20, num_std=2):
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    std = variance ** 0.5
    return middle + num_std * std, middle, middle - num_std * std

def calculate_bb_pct_b(closes, period=20):
    result = calculate_bollinger_bands(closes, period)
    if result == (None, None, None):
        return None
    upper, middle, lower = result
    band_width = upper - lower
    if band_width == 0:
        return 0.5
    return (closes[-1] - lower) / band_width

def calculate_bb_width(closes, period=20):
    result = calculate_bollinger_bands(closes, period)
    if result == (None, None, None):
        return None
    upper, middle, lower = result
    if middle == 0:
        return 0.0
    return (upper - lower) / middle

def calculate_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return None
    true_ranges = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        true_ranges.append(tr)
    if len(true_ranges) < period:
        return None
    atr = sum(true_ranges[-period:]) / period
    if closes[-1] == 0:
        return 0.0
    return atr / closes[-1]

def _rsi_series(closes, period, count):
    result = []
    for i in range(count):
        end = len(closes) - (count - 1 - i)
        lookback_start = max(0, end - period * 4)
        r = calculate_rsi(closes[lookback_start:end], period)
        if r is not None:
            result.append(r)
    return result

def calculate_stoch_rsi(closes, period=14):
    if len(closes) < period * 2 + 3:
        return None, None
    rsi_vals = _rsi_series(closes, period, period + 3)
    if len(rsi_vals) < period + 3:
        return None, None
    k_vals = []
    for i in range(3):
        window = rsi_vals[i: i + period]
        lo, hi = min(window), max(window)
        curr = rsi_vals[i + period]
        if hi == lo:
            k_vals.append(50.0)
        else:
            k_vals.append((curr - lo) / (hi - lo) * 100.0)
    return k_vals[-1], sum(k_vals) / 3

def calculate_williams_r(highs, lows, closes, period=14):
    if len(closes) < period:
        return None
    h = max(highs[-period:])
    l = min(lows[-period:])
    if h == l:
        return -50.0
    return (h - closes[-1]) / (h - l) * -100.0

def calculate_roc(closes, period=10):
    if len(closes) < period + 1:
        return None
    prev = closes[-period - 1]
    if prev == 0:
        return 0.0
    return (closes[-1] - prev) / prev

def calculate_obv_slope(closes, volumes, lookback=10):
    if len(closes) < lookback + 1 or len(volumes) < lookback + 1:
        return None
    obv = 0.0
    obv_series = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv += volumes[i]
        elif closes[i] < closes[i - 1]:
            obv -= volumes[i]
        obv_series.append(obv)
    window = obv_series[-lookback:]
    n = len(window)
    return (window[-1] - window[0]) / (n - 1) if n > 1 else 0.0

def calculate_vwap_diff(closes, vwaps):
    if not closes or not vwaps:
        return 0.0
    vwap = vwaps[-1]
    if vwap == 0:
        return 0.0
    return (closes[-1] - vwap) / vwap

def calculate_volume_ratio(volumes, period=14):
    if len(volumes) < period + 1:
        return None
    avg = sum(volumes[-period - 1:-1]) / period
    if avg == 0:
        return 1.0
    return volumes[-1] / avg

def _safe(val, default=0.0):
    return val if val is not None else default

def calculate_composite_score(closes, highs=None, lows=None, volumes=None,
                               vwaps=None, closes_5m=None, closes_15m=None):
    """
    Returns a composite score 0–100. Higher = stronger buy signal.
    If ML model loaded, uses 22-feature LightGBM score.
    Falls back to naive heuristic if no model.
    """
    if len(closes) < 31:
        return 0.0

    model = load_model()
    if model is not None:
        current_price = closes[-1]

        # --- Trend ---
        sma_14 = calculate_sma(closes[-14:], 14)
        sma_30 = calculate_sma(closes[-30:], 30)
        ema_21 = calculate_ema(closes, 21) if len(closes) >= 21 else None
        ema_50 = calculate_ema(closes, 50) if len(closes) >= 50 else calculate_ema(closes, len(closes))
        sma14_diff = (current_price - sma_14) / sma_14 if sma_14 else 0.0
        sma30_diff = (current_price - sma_30) / sma_30 if sma_30 else 0.0
        ema21_diff = (current_price - ema_21) / ema_21 if ema_21 else 0.0
        ema50_diff = (current_price - ema_50) / ema_50 if ema_50 else 0.0

        macd_line, macd_sig, macd_hist = calculate_macd(closes) if len(closes) >= 35 else (0.0, 0.0, 0.0)

        # --- Volatility / Bands ---
        bb_b = _safe(calculate_bb_pct_b(closes), 0.5)
        bb_w = _safe(calculate_bb_width(closes), 0.0)
        atr_norm = _safe(calculate_atr(highs, lows, closes) if highs and lows else None, 0.0)
        volat = calculate_volatility(closes[-14:])

        # --- Momentum ---
        rsi14 = _safe(calculate_rsi(closes[-28:], 14), 50.0)
        stoch_k, stoch_d = calculate_stoch_rsi(closes)
        stoch_k = _safe(stoch_k, 50.0)
        stoch_d = _safe(stoch_d, 50.0)
        willi = _safe(calculate_williams_r(highs, lows, closes) if highs and lows else None, -50.0)
        roc10 = _safe(calculate_roc(closes, 10), 0.0)

        # --- Volume ---
        obv_sl = _safe(calculate_obv_slope(closes, volumes) if volumes else None, 0.0)
        vwap_d = calculate_vwap_diff(closes, vwaps) if vwaps else 0.0
        vol_r = _safe(calculate_volume_ratio(volumes) if volumes else None, 1.0)

        # --- Multi-timeframe ---
        rsi_5m = 50.0
        sma20_diff_5m = 0.0
        if closes_5m and len(closes_5m) >= 20:
            rsi_5m = _safe(calculate_rsi(closes_5m[-28:], 14) if len(closes_5m) >= 28 else None, 50.0)
            sma20_5m = calculate_sma(closes_5m[-20:], 20)
            if sma20_5m:
                sma20_diff_5m = (closes_5m[-1] - sma20_5m) / sma20_5m

        rsi_15m = 50.0
        if closes_15m and len(closes_15m) >= 28:
            rsi_15m = _safe(calculate_rsi(closes_15m[-28:], 14), 50.0)

        features = [[
            sma14_diff, sma30_diff, ema21_diff, ema50_diff,
            rsi14, stoch_k, stoch_d, willi, roc10,
            _safe(macd_line, 0.0), _safe(macd_sig, 0.0), _safe(macd_hist, 0.0),
            bb_b, bb_w, atr_norm,
            obv_sl, vwap_d, vol_r,
            volat,
            rsi_5m, sma20_diff_5m, rsi_15m
        ]]

        prob = model.predict_proba(features)[0][1]
        return prob * 100.0

    # --- Fallback: Naive Heuristic ---
    sma14 = calculate_sma(closes, 14)
    rsi14 = calculate_rsi(closes, 14)
    volatility = calculate_volatility(closes)

    current_price = closes[-1]
    score = 0.0

    if sma14 is not None and current_price > sma14:
        score += 5.0
    else:
        score -= 5.0

    if rsi14 is not None:
        if rsi14 < 30:
            score += 10.0
        elif rsi14 > 70:
            score -= 10.0
        else:
            score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0

    score -= volatility * 100.0
    return score
