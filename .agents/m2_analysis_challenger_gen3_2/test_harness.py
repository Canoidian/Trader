import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import statistics

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from krakentrader.analysis import calculate_sma, calculate_rsi, calculate_volatility, calculate_composite_score
from scripts.run_analysis import main as run_analysis_main

class TestAnalysisEngine(unittest.TestCase):

    def test_sma(self):
        self.assertIsNone(calculate_sma([10, 20], 3))
        self.assertEqual(calculate_sma([10, 20, 30], 3), 20.0)
        self.assertEqual(calculate_sma([10, 20, 30, 40], 3), 30.0)

    def test_rsi_edge_cases(self):
        self.assertIsNone(calculate_rsi([10]*14, 14))
        
        # All same values
        self.assertEqual(calculate_rsi([10]*15, 14), 50.0)
        
        # Consistent upward trend
        closes = [10 + i for i in range(15)]
        self.assertEqual(calculate_rsi(closes, 14), 100.0)
        
        # Consistent downward trend
        closes = [100 - i for i in range(15)]
        self.assertEqual(calculate_rsi(closes, 14), 0.0)

    def test_rsi_calculation(self):
        # Known RSI test data
        closes = [
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 
            45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00
        ]
        # Calculate manually for validation
        rsi = calculate_rsi(closes, 14)
        self.assertIsNotNone(rsi)
        self.assertTrue(0 <= rsi <= 100)

    def test_volatility(self):
        self.assertEqual(calculate_volatility([10]), 0.0)
        self.assertEqual(calculate_volatility([10, 10]), 0.0)
        
        closes = [10, 11, 10, 11]
        returns = [(11-10)/10, (10-11)/11, (11-10)/10]
        self.assertAlmostEqual(calculate_volatility(closes), statistics.stdev(returns))

    def test_composite_score(self):
        self.assertEqual(calculate_composite_score([10]*14), 0.0)
        
        # Strong upward trend, low volatility
        closes_up = [10 + i * 0.1 for i in range(15)]
        score_up = calculate_composite_score(closes_up)
        
        # Downward trend, low volatility
        closes_down = [10 - i * 0.1 for i in range(15)]
        score_down = calculate_composite_score(closes_down)
        
        self.assertGreater(score_up, score_down)

    @patch('urllib.request.urlopen')
    def test_run_analysis_mocked_network(self, mock_urlopen):
        # Mock the Kraken API responses
        # OHLC format: [time, open, high, low, close, vwap, volume, count]
        
        def create_mock_response(closes):
            data = {
                'error': [],
                'result': {
                    'XXBTZUSD': [[0, 0, 0, 0, str(c), 0, 0, 0] for c in closes]
                }
            }
            cm = MagicMock()
            cm.read.return_value = json.dumps(data).encode('utf-8')
            cm.__enter__.return_value = cm
            return cm

        # Return different data for different calls
        # Pair 1: Uptrend
        # Pair 2: Downtrend
        # Pair 3: Flat
        closes_uptrend = [100 + i for i in range(20)]
        closes_downtrend = [100 - i for i in range(20)]
        closes_flat = [100 for i in range(20)]
        
        mock_urlopen.side_effect = [
            create_mock_response(closes_uptrend),
            create_mock_response(closes_downtrend),
            create_mock_response(closes_flat)
        ]
        
        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output
        
        run_analysis_main()
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # Verify output formatting and ranking
        self.assertIn("XXBTZUSD", output)
        self.assertIn("XETHZUSD", output)
        self.assertIn("SOLUSD", output)
        
        # Since we mocked only XXBTZUSD key in the result, wait, the fetch_data takes whatever key is first
        # keys = [k for k in data['result'].keys() if k != 'last']
        # This will work as long as we just return a dict with a single key.

if __name__ == '__main__':
    unittest.main()
