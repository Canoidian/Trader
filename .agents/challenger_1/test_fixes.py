import traceback
from krakentrader.api import calculate_fee
from krakentrader.backtest import run_backtest

# Test 1: Rate limit 429 unbound local error
print("Testing UnboundLocalError fix...")

import requests
from unittest.mock import patch
from krakentrader.api import get_historical_ohlcv

def test_unbound():
    with patch('requests.get') as mock_get:
        mock_resp = mock_get.return_value
        mock_resp.status_code = 429
        
        try:
            get_historical_ohlcv("BTCUSD")
        except Exception as e:
            print("Caught exception:", type(e), e)
            if isinstance(e, UnboundLocalError):
                print("FAIL: UnboundLocalError raised!")
            else:
                print("PASS: UnboundLocalError not raised")

test_unbound()


# Test 2: Fee Tier Math Edge Case
print("\nTesting Fee Tier Math Edge Case...")
# What if balance is extremely small? Underflow?
try:
    ohlcv = [
        [1000, "1.0", "1.0", "1.0", "1.0", "1.0", "1.0", 1],
        [1000, "1.0", "1.0", "1.0", "1.0", "1.0", "1.0", 1]
    ]
    res = run_backtest(ohlcv, initial_balance=1e-324, num_trades=1) # 1e-324 is the smallest denormalized float, might be 0.0
    print("Underflow test complete")
except Exception as e:
    print("Caught exception in backtest:", type(e), e)

try:
    ohlcv = [
        [1000, "1.0", "1.0", "1.0", "1.0", "1.0", "1.0", 1],
        [1000, "1.0", "1.0", "1.0", "1.0", "1.0", "1.0", 1]
    ]
    res = run_backtest(ohlcv, initial_balance=1e-300, num_trades=1)
    print("Very small balance test complete")
except Exception as e:
    print("Caught exception in backtest (small bal):", type(e), e)

