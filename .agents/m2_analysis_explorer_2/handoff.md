# Handoff Report: Milestone 2 Implementation Strategy

## Observation
1. The project directory currently contains only documentation files (`PROJECT.md`, `TEST_INFRA.md`, and `.agents/`). The `krakentrader/` and `scripts/` directories do not exist yet.
2. `PROJECT.md` and `SCOPE.md` specify that M2 (Lightweight Analysis Engine) has no dependencies (e.g., on M1) and should evaluate at least 3 coins locally to output a ranked recommendation.
3. The engine must run without high memory or GPU.
4. `SCOPE.md` allows the analyzer to use its own simple data fetching from the Kraken public API if the centralized API module (`get_recent_ohlcv`) is not yet available.
5. The output must be verifiable through stdout parsing, as required by `TEST_INFRA.md`.

## Logic Chain
1. **Directory Setup**: Since directories don't exist, the implementation must start by creating the `krakentrader` package (with an empty `__init__.py`) and the `scripts` directory.
2. **Lightweight Constraint**: To strictly adhere to "without high memory/GPU" and ensure a seamless execution environment without complex dependency management, the strategy should rely on Python's standard library (`urllib.request` for API calls, `math` and `statistics` for analysis) rather than heavy frameworks like `pandas` or `numpy`.
3. **Data Fetching**: Since `api.py` does not exist, `scripts/run_analysis.py` should directly query Kraken's public OHLC endpoint (`https://api.kraken.com/0/public/OHLC`) for at least 3 pairs (e.g., `XXBTZUSD` for BTC, `XETHZUSD` for ETH, and `SOLUSD` for SOL) to get recent daily closing prices.
4. **Technical Analysis**: `krakentrader/analysis.py` should implement pure Python functions for:
   - **SMA (Simple Moving Average)**: Standard average of recent closes.
   - **RSI (Relative Strength Index)**: Ratio of average upward price changes to downward price changes over a period.
   - **Volatility**: Standard deviation of daily returns.
   - **Scoring System**: A composite function (e.g., rewarding coins with Price > SMA, lower RSI indicating oversold conditions, and normalizing volatility) to output a sortable score.
5. **CLI Output**: `scripts/run_analysis.py` should tie this together, invoking the scoring function and printing a cleanly formatted, line-by-line ranking to stdout. This satisfies the `TEST_INFRA.md` requirement for subprocess verification via stdout parsing.

## Caveats
- Relying on pure Python (standard library) instead of `pandas`/`numpy` means more boilerplate math code, but guarantees low memory footprint. If the project team prefers `pandas` for readability and it fits memory constraints, that could be a viable alternative.
- Hardcoding the Kraken trading pairs (e.g., `XXBTZUSD`) in the script for the 3 coins is assumed acceptable for fulfilling the milestone.

## Conclusion
The implementer should proceed with the following steps:
1. **Create Directories**: `mkdir krakentrader scripts` and `touch krakentrader/__init__.py`.
2. **Create `krakentrader/analysis.py`**:
   - Implement `calculate_sma(closes, period)`
   - Implement `calculate_rsi(closes, period=14)`
   - Implement `calculate_volatility(closes)`
   - Implement `score_and_rank(coin_data_dict)` which returns a sorted list of `(coin, score)` tuples.
3. **Create `scripts/run_analysis.py`**:
   - Iterate over a list of 3 pairs: `["XXBTZUSD", "XETHZUSD", "SOLUSD"]`.
   - Use `urllib.request.urlopen` to fetch `https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440`.
   - Parse the JSON response to extract the closing prices.
   - Pass the data dict to `krakentrader.analysis.score_and_rank`.
   - Print the ranked recommendations to `sys.stdout`.

## Verification Method
1. Ensure the required files exist:
   - `krakentrader/__init__.py`
   - `krakentrader/analysis.py`
   - `scripts/run_analysis.py`
2. Run the analysis script: `python scripts/run_analysis.py`
3. Verification is successful if the script exits with status `0` and outputs a visible ranking of the 3 coins to stdout without triggering memory issues or requiring a GPU.
