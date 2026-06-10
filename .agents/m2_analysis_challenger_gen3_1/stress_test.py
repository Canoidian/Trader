import sys
import os
import random
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from krakentrader.analysis import (
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
    calculate_composite_score
)

class TestAnalysisEngine(unittest.TestCase):
    
    def test_sma(self):
        # Normal
        self.assertEqual(calculate_sma([10, 20, 30], 2), 25.0)
        # Not enough data
        self.assertIsNone(calculate_sma([10, 20], 3))
        # Zeroes
        self.assertEqual(calculate_sma([0, 0, 0], 2), 0.0)

    def test_rsi_flat(self):
        closes = [100.0] * 20
        self.assertEqual(calculate_rsi(closes, 14), 50.0)

    def test_rsi_up(self):
        closes = [float(i) for i in range(100, 120)]
        self.assertEqual(calculate_rsi(closes, 14), 100.0)

    def test_rsi_down(self):
        closes = [float(i) for i in range(120, 100, -1)]
        # RSI for purely down should be 0.0
        self.assertEqual(calculate_rsi(closes, 14), 0.0)

    def test_volatility_flat(self):
        closes = [100.0] * 20
        self.assertEqual(calculate_volatility(closes), 0.0)
        
    def test_volatility_zeroes(self):
        closes = [0.0] * 20
        self.assertEqual(calculate_volatility(closes), 0.0)
        
    def test_composite_score_insufficient_data(self):
        closes = [100.0] * 14
        self.assertEqual(calculate_composite_score(closes), 0.0)

    def test_composite_score_exact_15(self):
        closes = [100.0] * 15
        score = calculate_composite_score(closes)
        # SMA = 100, current = 100 -> current > sma is False -> score -= 5.0
        # RSI = 50 -> score += 10.0 - (20/40)*20 = 0.0
        # Vol = 0 -> score -= 0
        # Total = -5.0
        self.assertEqual(score, -5.0)

    def test_stress_random(self):
        # Fuzz testing with random arrays
        for _ in range(1000):
            length = random.randint(1, 100)
            closes = [random.uniform(0.0, 1000.0) for _ in range(length)]
            # Should not raise any exceptions
            calculate_sma(closes, 14)
            calculate_rsi(closes, 14)
            calculate_volatility(closes)
            calculate_composite_score(closes)

if __name__ == '__main__':
    unittest.main()
