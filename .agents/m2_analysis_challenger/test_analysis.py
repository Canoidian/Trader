import sys
import os
import random
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from krakentrader.analysis import calculate_sma, calculate_rsi, calculate_volatility, calculate_composite_score

class TestAnalysis(unittest.TestCase):
    def test_sma_zero_period(self):
        # Stress test: passing period=0 should be handled, but it raises ZeroDivisionError
        closes = [100.0, 105.0, 110.0]
        with self.assertRaises(ZeroDivisionError):
            calculate_sma(closes, 0)

    def test_rsi_zero_period(self):
        # Stress test: passing period=0 raises ZeroDivisionError
        closes = [100.0, 105.0, 110.0]
        with self.assertRaises(ZeroDivisionError):
            calculate_rsi(closes, 0)

    def test_rsi_fixed_edge_cases(self):
        # Test flat asset (was bug #3)
        closes = [100.0] * 20
        rsi = calculate_rsi(closes, 14)
        self.assertEqual(rsi, 50.0)

    def test_sma_truthiness_fix(self):
        # Test SMA=0 logic (was bug #2)
        closes = [0.0] * 20
        sma = calculate_sma(closes, 14)
        self.assertEqual(sma, 0.0)
        score = calculate_composite_score(closes)
        # Score calculation:
        # sma14 = 0.0, current_price = 0.0. current_price > sma14 is False -> score -= 5.0
        # rsi14 = 50.0 -> score += 10.0 - ((50-30)/40)*20 = 0.0
        # vol = 0.0 -> score -= 0.0
        self.assertEqual(score, -5.0)

if __name__ == '__main__':
    unittest.main()
