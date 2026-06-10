import pytest
import responses
from krakentrader.api import calculate_fee, get_historical_ohlcv
from krakentrader.backtest import run_backtest

def test_calculate_fee_edge_cases():
    # 0 trade size
    assert calculate_fee(0) == 0.0
    
    # Negative trade size (this might logically be an error, but mathematically works)
    assert calculate_fee(-100) == -0.40

def test_backtest_negative_and_zero_prices():
    # Construct synthetic OHLCV data
    # [time, open, high, low, close, vwap, volume, count]
    
    # Zero open price
    data_zero_open = [
        [1600000000, "0.0", "1.0", "0.0", "1.0", "0.5", "100", 10],
        [1600000000, "0.0", "1.0", "0.0", "1.0", "0.5", "100", 10]
    ]
    with pytest.raises(ZeroDivisionError):
        run_backtest(data_zero_open, num_trades=1)
        
    # Negative open price
    data_negative_open = [
        [1600000000, "-10.0", "1.0", "-15.0", "1.0", "0.5", "100", 10],
        [1600000000, "-10.0", "1.0", "-15.0", "1.0", "0.5", "100", 10]
    ]
    res = run_backtest(data_negative_open, num_trades=1)
    # The math will buy negative amounts of crypto
    assert res['trades'][0]['open_price'] == -10.0
    
    # Negative close price (sells for negative fiat, fee applied)
    data_negative_close = [
        [1600000000, "10.0", "10.0", "10.0", "-5.0", "0.5", "100", 10],
        [1600000000, "10.0", "10.0", "10.0", "-5.0", "0.5", "100", 10]
    ]
    res2 = run_backtest(data_negative_close, num_trades=1)
    assert res2['trades'][0]['close_price'] == -5.0

def test_backtest_balance_goes_negative():
    data = [
        [1600000000, "10.0", "10.0", "10.0", "5.0", "0.5", "100", 10],
        [1600000000, "10.0", "10.0", "10.0", "5.0", "0.5", "100", 10],
        [1600000000, "10.0", "10.0", "10.0", "5.0", "0.5", "100", 10]
    ]
    # Balance 0, but will trade $100 anyway
    res = run_backtest(data, initial_balance=0.0, num_trades=2)
    # Balance wasn't checked, went below zero
    assert res['final_balance'] < 0.0

@responses.activate
def test_api_rate_limit_handling():
    pair = "XXBTZUSD"
    # Simulate HTTP 429 Too Many Requests
    responses.add(
        responses.GET,
        f"https://api.kraken.com/0/public/OHLC?pair={pair}",
        status=429,
        json={"error": ["Rate limit exceeded"]}
    )
    
    import requests
    # get_historical_ohlcv uses requests.get and raise_for_status, which raises HTTPError
    with pytest.raises(requests.exceptions.HTTPError):
        get_historical_ohlcv(pair)

@responses.activate
def test_api_200_with_kraken_error():
    pair = "XXBTZUSD"
    # Simulate Kraken 200 OK but with API error
    responses.add(
        responses.GET,
        f"https://api.kraken.com/0/public/OHLC?pair={pair}",
        status=200,
        json={"error": ["EAPI:Rate limit exceeded"]}
    )
    
    with pytest.raises(Exception, match="Kraken API error: \\['EAPI:Rate limit exceeded'\\]"):
        get_historical_ohlcv(pair)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
