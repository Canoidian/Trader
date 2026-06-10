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
