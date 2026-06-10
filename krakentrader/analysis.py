import math
import statistics

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
    We'll use a simple heuristic:
    - Favorable if price is above SMA(14)
    - RSI near 40-60 is neutral, < 30 is oversold (good for buying), > 70 is overbought (bad)
    - Volatility adjustment: penalize high volatility slightly
    """
    if len(closes) < 15:
        return 0.0
        
    sma14 = calculate_sma(closes, 14)
    rsi14 = calculate_rsi(closes, 14)
    volatility = calculate_volatility(closes)
    
    current_price = closes[-1]
    
    score = 0.0
    
    # Trend component
    if sma14 is not None and current_price > sma14:
        score += 5.0
    else:
        score -= 5.0
        
    # RSI component
    if rsi14 is not None:
        if rsi14 < 30:
            score += 10.0
        elif rsi14 > 70:
            score -= 10.0
        else:
            score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0
            
    # Volatility penalty
    score -= volatility * 100.0
    
    return score
