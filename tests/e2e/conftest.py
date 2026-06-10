import pytest
import os
import csv
import json
import subprocess
import sys
from pathlib import Path

def generate_mock_data(tmp_path, coins, num_rows, trend="flat", price_start=100.0, fee_rate=0.001):
    data_dir = tmp_path / f"data_{trend}_{num_rows}_{'-'.join(coins)}"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    for i, coin in enumerate(coins):
        csv_file = data_dir / f"{coin}_historical.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            
            current_price = price_start + i * 10
            for r in range(num_rows):
                if trend == "bull":
                    current_price *= 1.01
                elif trend == "bear":
                    current_price *= 0.99
                elif trend == "crab":
                    current_price += (r % 3 - 1) * 2
                elif trend == "zero_variance":
                    pass
                elif trend == "single_direction":
                    current_price += 1
                elif trend == "unprofitable":
                    current_price *= 0.98
                elif trend == "profitable":
                    current_price *= 1.02
                elif trend == "identical":
                    current_price = price_start
                elif trend == "micro":
                    current_price = 0.000001 + (r * 0.0000001)
                
                if current_price <= 0:
                    current_price = 0.01

                open_p = current_price
                high_p = current_price * 1.02
                low_p = current_price * 0.98
                close_p = current_price
                
                writer.writerow([1600000000 + r * 60, open_p, high_p, low_p, close_p, 1000])

    config_file = data_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump({"api_key": "mock_key", "secret": "mock_secret", "fee_rate": fee_rate}, f)
        
    return data_dir

@pytest.fixture
def base_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL", "ADA", "DOGE"], 100, "bull")

@pytest.fixture
def profitable_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL", "ADA", "DOGE"], 100, "profitable")

@pytest.fixture
def unprofitable_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL", "ADA", "DOGE"], 100, "unprofitable")

@pytest.fixture
def single_direction_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC"], 100, "single_direction")

@pytest.fixture
def identical_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 100, "identical")

@pytest.fixture
def high_fees_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC"], 1000, "crab", fee_rate=0.05)

@pytest.fixture
def hft_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC"], 10000, "crab")

@pytest.fixture
def micro_trades_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC"], 100, "micro")

@pytest.fixture
def large_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 5000, "bull")

@pytest.fixture
def minimal_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 1, "flat")

@pytest.fixture
def zero_variance_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 100, "zero_variance")

@pytest.fixture
def bull_market_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 200, "bull")

@pytest.fixture
def bear_market_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 200, "bear")

@pytest.fixture
def crab_market_data_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 200, "crab")

@pytest.fixture
def exact_10_trades_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC"], 10, "bull")

@pytest.fixture
def three_coins_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL"], 100, "bull")

@pytest.fixture
def two_coins_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH"], 100, "bull")

@pytest.fixture
def five_coins_dir(tmp_path):
    return generate_mock_data(tmp_path, ["BTC", "ETH", "SOL", "ADA", "DOGE"], 100, "bull")

@pytest.fixture
def run_script():
    def _run_script(script_path, *args, **kwargs):
        # Allow passing custom env
        env = kwargs.pop('env', os.environ.copy())
        return subprocess.run(
            [sys.executable, script_path, *args],
            capture_output=True,
            text=True,
            env=env,
            **kwargs
        )
    return _run_script
