# KrakenTraderV2

A fully autonomous, high-frequency cryptocurrency trading bot and Multi-Asset Portfolio Manager built specifically for the Kraken exchange.

## Features

- **Multi-Asset Portfolio Management**: The bot doesn't just trade USD. It automatically scans your Kraken wallet for any assets you hold (e.g., USD, EUR, BTC) and dynamically finds pairs to trade them against.
- **Dynamic Trade Sizing**: Automatically calculates 95% of your available balance for a specific asset to execute maximum-efficiency trades while leaving a small buffer for fees.
- **Trailing Stop-Loss**: Replaces rigid stop-losses. The bot tracks the highest price a coin reaches while you hold it and trails a 3.0% stop-loss strictly behind the peak, allowing you to ride large market pumps while locking in profit.
- **Stale Trade Cutoffs**: Automatically cuts losses and liquidates trades that have been stagnant for over 6 hours, freeing up capital for better opportunities.
- **Crash Recovery**: Saves open positions to a local `state.json` file. If your machine reboots or the script crashes, the bot instantly picks up exactly where it left off.
- **Rate-Limit Safe**: Evaluates random market samples per loop to prevent hitting Kraken's strict API rate limits.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Canoidian/Trader.git
cd Trader
```

### 2. Set Up the Environment
Create a Python virtual environment and install the required dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```
*(Note for older Macs: If you get an OpenSSL warning from urllib3, run `pip install "urllib3<2"`)*

### 3. API Keys
Create a `.env` file in the root directory:
```bash
nano .env
```
Paste your Kraken API keys into the file:
```env
KRAKEN_API_KEY=your_public_key_here
KRAKEN_API_SECRET=your_private_key_here
```
> **IMPORTANT**: Your Kraken API key must have the **"Create & Modify Orders"** and **"Query Funds"** permissions enabled.

## Running the Bot

To start the live Multi-Asset Portfolio loop:
```bash
python scripts/run_live.py
```
The bot will initialize, load any existing trades from `state.json`, and immediately begin scanning the market.

## Project Architecture

- `krakentrader/api.py`: Handles secure HMAC-SHA512 authenticated requests to Kraken, balance checking, and dynamic quote asset matching.
- `krakentrader/analysis.py`: Contains the mathematical core. Uses Simple Moving Averages (SMA), Relative Strength Index (RSI), and Volatility to generate a Composite Score.
- `krakentrader/backtest.py`: Simulator module to test strategies against historical data and calculate net profit after Kraken fees.
- `scripts/run_live.py`: The main asynchronous portfolio loop. Manages state, monitors open positions, and executes live trades.

## Security Warning
This bot executes real market orders using real capital. The `.gitignore` file is configured to prevent your `.env` and `state.json` files from uploading to GitHub, but you are responsible for keeping your API keys secure. Never share your private keys.
