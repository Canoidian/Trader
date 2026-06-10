import unittest
from krakentrader.analysis import calculate_sma, calculate_rsi, calculate_volatility, calculate_composite_score

class TestAnalysisAdversarial(unittest.TestCase):
    def test_sma_zero(self):
        # SMA of all zeros
        closes = [0.0] * 15
        self.assertEqual(calculate_sma(closes, 14), 0.0)
        self.assertEqual(calculate_composite_score(closes), -5.0) # SMA=0, current=0 -> not current_price > sma14 -> -5. rsi=50 -> +2, wait: 10 - (20/40)*20 = 0. So score is -5.0
        
    def test_rsi_constant(self):
        # Constant price -> RSI should be 50
        closes = [100.0] * 15
        self.assertEqual(calculate_rsi(closes, 14), 50.0)
        
    def test_rsi_pure_gain(self):
        # Pure gain
        closes = [float(i) for i in range(100, 115)]
        self.assertEqual(calculate_rsi(closes, 14), 100.0)

    def test_rsi_pure_loss(self):
        # Pure loss
        closes = [float(100 - i) for i in range(15)]
        self.assertEqual(calculate_rsi(closes, 14), 0.0)

    def test_volatility_empty_or_small(self):
        self.assertEqual(calculate_volatility([]), 0.0)
        self.assertEqual(calculate_volatility([100.0]), 0.0)

    def test_composite_score_insufficient_data(self):
        self.assertEqual(calculate_composite_score([100.0] * 14), 0.0)

if __name__ == '__main__':
    unittest.main()
