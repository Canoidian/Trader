import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from krakentrader.regime import calculate_adx, classify_regime, get_market_regime

def test_calculate_adx_trending():
    # Strong uptrend: price rises consistently
    n = 50
    closes = [100.0 + i * 0.5 for i in range(n)]
    highs = [c + 0.3 for c in closes]
    lows = [c - 0.3 for c in closes]
    adx = calculate_adx(highs, lows, closes)
    assert adx is not None
    assert adx > 0

def test_calculate_adx_too_short():
    assert calculate_adx([11.0]*5, [9.0]*5, [10.0]*5) is None

def test_classify_regime_bull():
    # ADX >= 20, price above SMA200
    regime, threshold = classify_regime(adx=25.0, price=110.0, sma200=100.0)
    assert regime == 'BULL'
    assert threshold == 60.0

def test_classify_regime_bear():
    regime, threshold = classify_regime(adx=25.0, price=90.0, sma200=100.0)
    assert regime == 'BEAR'
    assert threshold == 78.0

def test_classify_regime_sideways():
    regime, threshold = classify_regime(adx=15.0, price=100.0, sma200=100.0)
    assert regime == 'SIDEWAYS'
    assert threshold == 65.0

def test_get_market_regime_uses_cache():
    import krakentrader.regime as regime_module
    regime_module._regime_cache = None  # reset between tests
    regime_module._regime_cache_time = 0.0

    mock_api = MagicMock()
    ohlcv = [[i, 10.0, 10.3, 9.7, 10.0 + i*0.01, 10.0, 1000.0, 10] for i in range(300)]
    mock_api.get_historical_ohlcv_interval.return_value = ohlcv

    regime1, t1 = get_market_regime(mock_api)
    regime2, t2 = get_market_regime(mock_api)

    # Second call uses cache — API called exactly once
    assert mock_api.get_historical_ohlcv_interval.call_count == 1
    assert regime1 == regime2
    assert t1 == t2
