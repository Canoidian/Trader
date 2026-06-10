# Handoff: Milestone 2 Implementation Strategy

## 1. Observation
- The workspace root `/Users/williamisaak/Projects/KrakenTraderV2/` currently contains no source code (the `krakentrader/` and `scripts/` directories do not exist).
- `PROJECT.md` and `.agents/m2_analysis/SCOPE.md` mandate building a "Lightweight Analysis Engine" evaluating at least 3 coins locally, calculating RSI, Moving Averages (SMA), and Volatility without high memory/GPU usage.
- The system expects data fetching for the 3 coins. `SCOPE.md` states: "Analyzer will fetch recent data for 3 coins. It expects `get_recent_ohlcv(pair)` to provide data, or it will use its own simple data fetching from Kraken public API for testing purposes".

## 2. Logic Chain
- **Codebase State**: Since the API module (`krakentrader/api.py`) from Milestone 1 is not yet implemented, the analysis engine must include a standalone, simple HTTP fetcher using the Kraken public API (`https://api.kraken.com/0/public/OHLC`) to pull OHLCV data.
- **Lightweight Constraint**: The "without high memory/GPU" constraint implies avoiding heavy ML frameworks (like PyTorch/TensorFlow). We can implement the indicators (SMA, RSI, Volatility) using either Python's built-in `math` and `statistics` libraries, or standard data processing libraries (`pandas`, `numpy`) if they are acceptable within the "lightweight" context. Given typical Python setups, `pandas` is standard, but a pure Python approach guarantees minimal footprint. The recommendation will suggest pure Python or minimal standard libraries.
- **Indicators Structure**: 
  - **SMA (Simple Moving Average)**: Average of the closing prices over a specific period (e.g., 14 days).
  - **RSI (Relative Strength Index)**: Magnitude of recent gains vs losses over a 14-period window.
  - **Volatility**: Standard deviation of closing prices or daily returns.
- **Ranking Logic**: A composite scoring function should normalize these three metrics to rank the 3 coins. For example, a formula that rewards high RSI (momentum), low Volatility (safety), and positive SMA trend.

## 3. Caveats
- `krakentrader/api.py` does not exist, so the recommended strategy embeds a simple `fetch_ohlcv` function into the `run_analysis.py` script or `analysis.py` module to unblock M2 independently.
- We assume standard Python libraries (`requests` for API fetching) are available. If no external packages are allowed, Python's built-in `urllib.request` should be used.

## 4. Conclusion
**Recommended Implementation Strategy:**

1. **Create `krakentrader/analysis.py`**:
   - Implement three technical indicator functions using plain Python lists or minimal `pandas`/`numpy` (depending on environment constraints):
     - `calculate_sma(prices: list, period: int) -> float`
     - `calculate_rsi(prices: list, period: int) -> float`
     - `calculate_volatility(prices: list) -> float`
   - Implement a ranking function:
     - `rank_coins(coin_metrics: dict) -> list`
     - Logic: Compute a simple "bullish score" (e.g., Score = (RSI / 100) * 0.5 + (Price / SMA) * 0.3 - Volatility * 0.2) and return coins sorted by score descending.

2. **Create `scripts/run_analysis.py`**:
   - Define a list of 3 coins (e.g., `["XXBTZUSD", "XETHZUSD", "SOLUSD"]`).
   - Implement a `fetch_kraken_ohlc(pair)` function using `urllib.request` or `requests` to call `https://api.kraken.com/0/public/OHLC?pair=<pair>`.
   - Parse the closing prices from the API response.
   - Loop over the 3 coins, fetch data, calculate SMA, RSI, and Volatility using `krakentrader.analysis`.
   - Pass the metrics to `rank_coins` and `print()` the final recommended rankings to stdout.

## 5. Verification Method
- **To test the implementation:** Run `python scripts/run_analysis.py` from the root directory.
- **Expected result:** The script should fetch live data for 3 pairs, compute the indicators, and print a ranked list of the 3 coins to the console, exiting with code 0.
