import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from krakentrader.analysis import (
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
    calculate_composite_score
)

def run_tests():
    print("Testing SMA...")
    try:
        print(calculate_sma([1.0]*15, 14))
    except Exception as e:
        print(f"SMA Error: {e}")

    print("Testing RSI...")
    try:
        print(calculate_rsi([1.0]*15, 14))
    except Exception as e:
        print(f"RSI Error: {e}")
    
    print("Testing Volatility...")
    try:
        print(calculate_volatility([1.0]*15))
    except Exception as e:
        print(f"Volatility Error: {e}")

    print("Testing Composite Score...")
    try:
        print(calculate_composite_score([1.0]*15))
    except Exception as e:
        print(f"Composite Score Error: {e}")

if __name__ == "__main__":
    run_tests()
