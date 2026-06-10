# E2E Test Strategy Handoff

## 1. Observation
- `ORIGINAL_REQUEST.md` specifies two features:
  - **F1 (Execution & Fee Verification)**: `scripts/run_backtest.py` must simulate $\ge$ 10 trades using historical Kraken data, explicitly subtract Kraken trading fees, and output a final PnL summary.
  - **F2 (Research Verification)**: `scripts/run_analysis.py` must evaluate $\ge$ 3 coins, output a ranked recommendation, and run locally without high memory/GPU requirements.
- `TEST_INFRA.md` dictates opaque-box `pytest` functions via `subprocess`, parsing stdout and exit codes.
- Coverage thresholds are defined for four tiers:
  - **Tier 1**: $\ge$ 5 per feature (Category-Partition).
  - **Tier 2**: $\ge$ 5 per feature (Boundary Value Analysis).
  - **Tier 3**: Pairwise coverage of major feature interactions.
  - **Tier 4**: $\ge$ 5 realistic application scenarios.

## 2. Logic Chain
- **Testing Approach**: Since tests are opaque-box CLI wrappers, they should invoke `python scripts/...` with mock data directories to avoid real network calls. The test suite will enforce the presence of CLI flags (e.g., `--data-dir`, `--coins`).
- **Tier 1 (Category-Partition)** focuses on normal usage, negative inputs, and basic variations (profitable vs unprofitable, 3 vs 5 coins, missing data).
- **Tier 2 (BVA)** directly tests the acceptance criteria boundaries: exactly 10 trades (F1), exactly 3 coins (F2), low capital limits, and memory usage limits for the "lightweight" requirement.
- **Tier 3 (Pairwise)** exercises the handoff from Analysis to Backtest. `run_analysis.py`'s output must be directly feedable into `run_backtest.py`.
- **Tier 4 (Scenarios)** models real-world multi-step workflows like running the pipeline on different market conditions and rebalancing over multiple time periods.

## 3. Caveats
- Since the implementation does not exist yet, the test cases assume certain CLI arguments (e.g., `--data-dir`, `--coins`, `--mock-fees`). If the implementer chooses a different CLI interface, the test suite will need updating.
- Testing "low memory/GPU requirements" in BVA (F2_T2_3) strictly via `subprocess` may require utilizing Python's `resource` module within the test to fail if memory exceeds a reasonable threshold (e.g., 512MB).
- The test strategy relies on `tests/e2e/conftest.py` generating deterministic mock historical CSV/JSON data fixtures so the tests run reliably offline.

## 4. Conclusion
The following test cases should be implemented in `tests/e2e/test_e2e.py`:

### Tier 1: Category-Partition
**Feature 1 (`run_backtest.py`)**
- `test_f1_t1_profitable_run`: Basic run yielding positive PnL. Verifies fee deduction logic and exit code 0.
- `test_f1_t1_unprofitable_run`: Basic run yielding negative PnL. Verifies loss accumulation.
- `test_f1_t1_zero_trades`: Data with no valid signals. PnL = 0, Fees = 0.
- `test_f1_t1_invalid_data`: Malformed data file. Expect non-zero exit code and error message.
- `test_f1_t1_single_direction_trades`: Only buys or only sells. Verifies fee logic on asymmetric trading.

**Feature 2 (`run_analysis.py`)**
- `test_f2_t1_basic_evaluation`: Evaluates 3 coins, outputs ranked list.
- `test_f2_t1_extended_evaluation`: Evaluates 5 coins. Verifies scaling.
- `test_f2_t1_identical_data`: All coins have identical mock data. Verifies tie-breaking logic.
- `test_f2_t1_missing_coin_data`: Data missing for 1 of the requested coins. Graceful degradation/error.
- `test_f2_t1_unsupported_ticker`: Requests analysis on invalid ticker. Fails with clear error.

### Tier 2: Boundary Value Analysis
**Feature 1 (`run_backtest.py`)**
- `test_f1_t2_exactly_10_trades`: Verifies AC1 lower bound (10 trades).
- `test_f1_t2_zero_capital`: Initial capital is 0. Script should fail gracefully.
- `test_f1_t2_fee_exceeds_profit`: Trades where gross profit is positive but net is negative after fees.
- `test_f1_t2_high_frequency_volume`: 10,000+ trades in mock data. Tests PnL accumulation precision.
- `test_f1_t2_micro_trades`: extremely small trade sizes verifying decimal/rounding logic for fees.

**Feature 2 (`run_analysis.py`)**
- `test_f2_t2_exactly_3_coins`: Verifies AC2 lower bound (3 coins).
- `test_f2_t2_insufficient_coins`: Tries to analyze 1 or 2 coins. Expect error.
- `test_f2_t2_memory_limit_large_data`: Pass 10 years of 1m mock data. Test fails if process memory exceeds 512MB (verifies AC2 lightweight requirement).
- `test_f2_t2_minimal_data`: Pass only 1 candle of data. Verifies behavior on extreme data shortage.
- `test_f2_t2_zero_variance_data`: Prices remain exactly flat for all timeframes.

### Tier 3: Pairwise Interactions
- `test_f1f2_t3_feed_top_rank`: Parse output of `run_analysis.py`, feed top coin as argument to `run_backtest.py`.
- `test_f1f2_t3_feed_bottom_rank`: Feed lowest-ranked coin to backtest.
- `test_f1f2_t3_concurrent_execution`: Run Analysis and Backtest as parallel subprocesses to ensure no file locking/cache collision issues.
- `test_f1f2_t3_shared_data_dir`: Ensure both scripts correctly parse the same mock data directory structure without conflict.

### Tier 4: Workload / Scenarios
- `test_t4_bull_market_scenario`: E2E run on simulated bull market data. Analysis picks coin -> backtest executes -> positive PnL.
- `test_t4_bear_market_scenario`: E2E run on simulated bear market data. Expect defensive behavior / minimized losses.
- `test_t4_crab_market_volatility`: E2E run on high volatility, zero-trend data. Critical test for fee accumulation destroying small profits.
- `test_t4_weekly_rebalance_loop`: Bash-script-like loop. Analysis -> backtest -> next week -> analysis -> backtest.
- `test_t4_analysis_fallback`: Analysis yields no viable coins. Backtest is invoked with empty list or safe mode.

## 5. Verification Method
When the developers implement the test suite based on this plan, execute:
```bash
pytest tests/e2e/test_e2e.py -v
```
All tests should initially fail due to missing scripts (`FileNotFoundError`), fulfilling their TDD purpose. As scripts are developed, stdout parsing (`assert "PnL" in result.stdout`) and exit code checks (`assert result.returncode == 0`) will verify functionality independently of internal Python logic.
