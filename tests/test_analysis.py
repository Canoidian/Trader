import pytest
from krakentrader.analysis import calculate_sma, calculate_rsi, calculate_volatility, calculate_composite_score

def test_calculate_sma():
    closes = [10.0, 11.0, 12.0, 13.0, 14.0]
    
    # Normal case
    assert calculate_sma(closes, 3) == (12.0 + 13.0 + 14.0) / 3
    
    # Period > len(closes)
    assert calculate_sma(closes, 10) is None
    
    # Period <= 0
    assert calculate_sma(closes, 0) is None
    assert calculate_sma(closes, -1) is None

def test_calculate_rsi():
    closes = [10.0 + i for i in range(20)]  # steadily increasing
    
    # Normal case
    rsi = calculate_rsi(closes, 14)
    assert rsi is not None
    assert rsi == 100.0  # since there are no losses
    
    # Period >= len(closes)
    assert calculate_rsi([10.0, 11.0], 14) is None
    
    # Period <= 0
    assert calculate_rsi(closes, 0) is None
    assert calculate_rsi(closes, -1) is None

def test_calculate_volatility():
    closes = [10.0, 10.0, 10.0]
    assert calculate_volatility(closes) == 0.0
    
    closes_var = [10.0, 11.0, 10.0, 11.0]
    vol = calculate_volatility(closes_var)
    assert vol > 0.0
    
    # Less than 2 elements
    assert calculate_volatility([10.0]) == 0.0

def test_calculate_composite_score():
    closes = [10.0] * 15
    score = calculate_composite_score(closes)
    assert isinstance(score, float)

    closes_short = [10.0] * 10
    assert calculate_composite_score(closes_short) == 0.0

from krakentrader.analysis import (
    calculate_ema, calculate_macd,
    calculate_bollinger_bands, calculate_bb_pct_b, calculate_bb_width,
    calculate_atr
)

def test_calculate_ema():
    closes = [10.0] * 5
    assert calculate_ema(closes, 5) == 10.0
    # Period > len
    assert calculate_ema([10.0, 11.0], 5) is None
    # Period <= 0
    assert calculate_ema([10.0, 11.0, 12.0], 0) is None
    # EMA in uptrend is above simple midpoint
    closes_up = [10.0 + i for i in range(20)]
    ema = calculate_ema(closes_up, 10)
    assert ema is not None
    assert ema > 14.0  # last value is 29, EMA lags but well above midpoint

def test_calculate_macd():
    # Too short — need >= 35 bars
    assert calculate_macd([10.0] * 20) == (None, None, None)
    # Uptrend: MACD line > 0 (fast EMA > slow EMA)
    closes_up = [10.0 + i * 0.2 for i in range(40)]
    macd_line, signal, histogram = calculate_macd(closes_up)
    assert macd_line is not None
    assert signal is not None
    assert histogram is not None
    assert macd_line > 0

def test_calculate_bollinger_bands():
    # Flat data: bands collapse to middle
    closes = [10.0] * 25
    upper, middle, lower = calculate_bollinger_bands(closes)
    assert upper == middle == lower == 10.0
    # Too short
    assert calculate_bollinger_bands([10.0] * 10) == (None, None, None)
    # With variance: upper > middle > lower
    import random as rnd; rnd.seed(42)
    closes_var = [10.0 + rnd.gauss(0, 0.5) for _ in range(25)]
    u, m, l = calculate_bollinger_bands(closes_var)
    assert u > m > l

def test_calculate_bb_pct_b():
    # At lower band: %B = 0, at upper band: %B = 1
    closes_flat = [10.0] * 25  # zero-width bands → return 0.5
    assert calculate_bb_pct_b(closes_flat) == 0.5
    # Too short
    assert calculate_bb_pct_b([10.0] * 10) is None

def test_calculate_bb_width():
    # Flat: width = 0
    assert calculate_bb_width([10.0] * 25) == 0.0
    # Too short
    assert calculate_bb_width([10.0] * 10) is None

def test_calculate_atr():
    # Constant candles: TR = high - low = 2, ATR = 2, normalized = 2/10 = 0.2
    highs = [11.0] * 20
    lows = [9.0] * 20
    closes = [10.0] * 20
    atr = calculate_atr(highs, lows, closes, period=14)
    assert atr is not None
    assert abs(atr - 0.2) < 0.01
    # Too short
    assert calculate_atr([11.0]*5, [9.0]*5, [10.0]*5, period=14) is None
