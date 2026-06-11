import math
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
        except Exception:
            pass
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

def calculate_composite_score(closes):
    """
    Returns a composite score for ranking. Higher is better.
    If the ML model is trained, it returns a probability (0.0 to 1.0) scaled up to 100.
    Otherwise, it falls back to the naive heuristic.
    """
    if len(closes) < 31:
        return 0.0
        
    model = load_model()
    if model is not None:
        # ML Scoring Path
        current_price = closes[-1]
        slice_14 = closes[-14:]
        slice_30 = closes[-30:]
        
        sma_14 = calculate_sma(slice_14, 14)
        sma_30 = calculate_sma(slice_30, 30)
        rsi = calculate_rsi(slice_14, 14)
        volat = calculate_volatility(slice_14)
        
        if sma_14 and sma_30 and rsi:
            sma_14_diff = (current_price - sma_14) / sma_14
            sma_30_diff = (current_price - sma_30) / sma_30
            features = [[sma_14_diff, sma_30_diff, rsi, volat]]
            
            # Predict probability of class 1 (pump)
            prob = model.predict_proba(features)[0][1]
            return prob * 100.0  # Scale to 0-100 so it works with the old run_live threshold conceptually, though we'll update run_live
            
    # Fallback Path (Naive)
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
