import sys
import os
sys.path.insert(0, os.path.abspath('/Users/williamisaak/Projects/KrakenTraderV2'))

import krakentrader.api as api
from krakentrader.backtest import run_backtest

def run():
    print("Testing calculate_fee")
    assert api.calculate_fee(100.0, is_maker=True) == 0.25
    assert api.calculate_fee(100.0, is_maker=False) == 0.40
    print("Fee calc passed")

    print("Testing get_historical_ohlcv")
    # Actually we can't test external API without network, but let's mock it
    
run()
