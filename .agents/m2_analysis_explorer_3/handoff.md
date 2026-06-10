# Handoff Report: Milestone 2 - Lightweight Analysis Engine Strategy

## 1. Observation
- Based on `PROJECT.md` and `.agents/m2_analysis/SCOPE.md`, Milestone 2 is independent of Milestone 1 and focuses on building a lightweight technical analysis engine.
- Currently, no Python files exist in the project root or `krakentrader/` directory.
- The requirements explicitly state the analysis must evaluate at least 3 coins, output a ranked recommendation, run locally without high memory/GPU, and use a fallback mechanism to fetch recent OHLCV data directly from Kraken's public API if the `krakentrader.api` module (from M1) is not yet available.

## 2. Logic Chain
- **Independence & Data Fetching:** Since M1 and M2 are running concurrently, `krakentrader.api` may not exist when this is implemented. The strategy must include a lightweight fallback data fetcher using the `requests` library to query Kraken's public `OHLC` endpoint (e.g., `https://api.kraken.com/0/public/OHLC?pair=...`).
- **Lightweight Engine Constraint:** To strictly adhere to "without high memory/GPU", the strategy should avoid heavy machine learning frameworks and can even avoid `pandas`/`numpy` by relying on Python's built-in `math` and `statistics` libraries for the required technical indicators. 
- **Indicator Design (`krakentrader/analysis.py`):**
  - **SMA (Simple Moving Average):** Average of the last N closing prices.
  - **RSI (Relative Strength Index):** Computed over a 14-period window using average gains and losses.
  - **Volatility:** Standard deviation of percentage returns over a lookback window.
- **Scoring & Ranking:** To output a "ranked recommendation", the engine needs a heuristic scoring function. For example: a formula that rewards price being above the SMA, penalizes extreme overbought RSI (>70), and balances for volatility.
- **Entrypoint (`scripts/run_analysis.py`):** A script that defines 3 target pairs (e.g., `"XXBTZUSD"`, `"XETHZUSD"`, `"SOLUSD"`), fetches their data, computes their scores using the engine, and sorts them descendingly to print a final recommendation table.

## 3. Caveats
- Kraken's public API has strict rate limits. A short `time.sleep()` might be necessary between the 3 coin fetches to avoid HTTP 429 Too Many Requests errors.
- The default Kraken pairs include prefixes (e.g., `XXBTZUSD` for BTC/USD). The parsing logic must adapt to the nested JSON response format from Kraken's public API.
- The scoring heuristic is purely demonstrative and not intended for actual financial risk without further backtesting.

## 4. Conclusion
Recommend implementing the following file structure and logic:

1. **`krakentrader/analysis.py`**
   - Provide a fallback fetch function `fetch_kraken_ohlc(pair)` using `requests`.
   - Implement `calculate_sma(prices, period)` and `calculate_rsi(prices, period=14)` using standard list comprehensions and `statistics`.
   - Implement `calculate_volatility(prices)` using standard deviation of returns.
   - Implement `compute_score(current_price, sma, rsi, volatility)` to generate a single composite float score.
   - Combine these into a main `analyze_and_score(pair, ohlc_data)` function.

2. **`scripts/run_analysis.py`**
   - Set up the environment (ensure `krakentrader` is in `sys.path`).
   - Define a list of 3 coins: `pairs = ["XXBTZUSD", "XETHZUSD", "SOLUSD"]`.
   - Loop over pairs, fetch data, run `analyze_and_score`.
   - Store results, sort by score descending.
   - Print a formatted console output (e.g., Rank 1: BTC, Score: 75.2, RSI: 52 ...).

## 5. Verification Method
- Execute the script using `python scripts/run_analysis.py`.
- **Validation criteria:** 
  1. The script runs locally without relying on external databases or GPUs.
  2. It prints an evaluation of exactly 3 different trading pairs.
  3. The output contains computed values for RSI, SMA, and Volatility.
  4. The output provides a clear 1 to 3 ranking based on the calculated score.
