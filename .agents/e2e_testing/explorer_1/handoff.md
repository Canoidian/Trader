# E2E Testing Strategy and Test Cases

## Observation
- `TEST_INFRA.md` specifies an opaque-box, requirement-driven test philosophy using Category-Partition (Tier 1), Boundary Value Analysis (Tier 2), Pairwise (Tier 3), and Workload Testing (Tier 4).
- The target test suite is `tests/e2e/test_e2e.py` running via `pytest`.
- The CLI entrypoints are `scripts/run_backtest.py` (Feature 1: Execution & Fee Verification) and `scripts/run_analysis.py` (Feature 2: Research Verification).
- Features F1 and F2 map directly to `ORIGINAL_REQUEST.md` R1/AC1 and R2/AC2.
- AC1 requires `run_backtest.py` to simulate at least 10 trades, explicitly subtract Kraken fees, and output a PnL summary.
- AC2 requires `run_analysis.py` to evaluate at least 3 coins, output a ranked recommendation, and run without high memory.
- Expected coverage: 5 tests per feature for Tiers 1 and 2, pairwise for Tier 3, and 5 realistic scenarios for Tier 4.

## Logic Chain
1.  Since the scripts do not exist, we must assume standard CLI interfaces to enable opaque-box testing:
    -   `scripts/run_backtest.py [--pair PAIR] [--trades NUM_TRADES] [--starting-balance BALANCE]`
    -   `scripts/run_analysis.py [--coins COIN1 COIN2 ...] [--limit TOP_N]`
2.  **Tier 1 (Equivalence Classes)** requires testing valid/invalid inputs for both scripts to reach ≥5 cases per feature. We will cover standard inputs, invalid strings, negative numbers, and help flags.
3.  **Tier 2 (Boundary Value Analysis)** requires testing the edges of the Acceptance Criteria. AC1 boundary is 10 trades; AC2 boundary is 3 coins. We also test zero-values and minimum valid inputs.
4.  **Tier 3 (Pairwise)** requires testing combinations of inputs. We will pair parameters (e.g., pairs + trade counts, coin counts + limits).
5.  **Tier 4 (Workload/Scenarios)** requires realistic usage. The most critical scenario is the pipeline: output of analysis feeds into backtesting. Other scenarios include high volatility, continuous loops, and balance exhaustion.

## Caveats
- The CLI interface arguments (`--pair`, `--trades`, `--coins`, etc.) are assumed. The implementation team must conform to these arguments or update the test suite accordingly.
- Data fetching for backtesting is assumed to happen automatically or use pre-bundled historical data; if it requires a `--data` flag, tests will need to provide mock data files.
- The pairwise combinations are limited to assumed parameters.

## Conclusion

The following `pytest` test cases should be implemented in `tests/e2e/test_e2e.py`:

### Tier 1: Category-Partition
**F1 (run_backtest.py):**
1.  `test_f1_t1_valid_standard_run`: Run with valid pair and `--trades 10`. Verify exit 0, stdout contains "PnL" and "Fees".
2.  `test_f1_t1_valid_large_trades`: Run with `--trades 50`. Verify exit 0, successful simulation.
3.  `test_f1_t1_invalid_pair`: Run with non-existent pair (e.g., `INVALID_PAIR`). Verify non-zero exit and error.
4.  `test_f1_t1_invalid_trades_negative`: Run with `--trades -1`. Verify non-zero exit code.
5.  `test_f1_t1_help_flag`: Run with `--help`. Verify exit 0 and usage string.

**F2 (run_analysis.py):**
6.  `test_f2_t1_valid_3_coins`: Run with `--coins BTC ETH SOL`. Verify exit 0, stdout contains ranked list.
7.  `test_f2_t1_valid_many_coins`: Run with `--coins BTC ETH SOL ADA DOT XRP`. Verify exit 0.
8.  `test_f2_t1_invalid_coin`: Run with invalid ticker (e.g., `FAKECOIN123`). Verify non-zero exit.
9.  `test_f2_t1_insufficient_coins`: Run with `--coins BTC` (1 coin). Verify non-zero exit (violates AC2).
10. `test_f2_t1_help_flag`: Run with `--help`. Verify exit 0 and usage string.

### Tier 2: Boundary Value Analysis
**F1 (run_backtest.py):**
11. `test_f1_t2_trades_exact_minimum`: Run with `--trades 10` (exact AC1 boundary).
12. `test_f1_t2_trades_below_minimum`: Run with `--trades 9` (just below AC1 threshold, should fail or warn).
13. `test_f1_t2_trades_zero`: Run with `--trades 0`. Verify failure.
14. `test_f1_t2_balance_zero`: Run with `--starting-balance 0`. Verify failure due to insufficient funds.
15. `test_f1_t2_balance_minimal`: Run with `--starting-balance 0.0001` (too small for Kraken minimum order size). Verify failure.

**F2 (run_analysis.py):**
16. `test_f2_t2_coins_exact_minimum`: Run with exactly 3 coins (AC2 boundary).
17. `test_f2_t2_coins_below_minimum`: Run with exactly 2 coins. Verify failure or warning.
18. `test_f2_t2_coins_empty`: Run with `--coins ""`. Verify failure.
19. `test_f2_t2_no_args`: Run with no arguments. Should use default 3 coins (or fail cleanly).
20. `test_f2_t2_max_coins`: Run with 50 coins to test memory/performance constraints.

### Tier 3: Pairwise Coverage
21. `test_t3_pairwise_default_pair_high_trades`: Pairwise backtest (e.g., BTC/USD + 100 trades).
22. `test_t3_pairwise_alt_pair_min_trades`: Pairwise backtest (e.g., SOL/USD + 10 trades).
23. `test_t3_pairwise_analysis_few_coins_high_limit`: Analysis with 3 coins, limit 3.
24. `test_t3_pairwise_analysis_many_coins_low_limit`: Analysis with 10 coins, limit 1.

### Tier 4: Workload & Real-World Scenarios
25. `test_t4_scenario_full_pipeline`: Run `run_analysis.py`, capture top ranked coin, pass it as `--pair` to `run_backtest.py`. Verify full pipeline succeeds.
26. `test_t4_scenario_continuous_analysis`: Run `run_analysis.py` 3 times sequentially to simulate periodic daemon polling.
27. `test_t4_scenario_high_volatility_pair`: Backtest on a typically volatile pair (e.g., DOGE/USD) to ensure fee tracking accurately reflects volatile slippage.
28. `test_t4_scenario_stablecoin_pair`: Backtest on a stablecoin pair (e.g., USDT/USD) to verify bot behavior when price changes are minimal.
29. `test_t4_scenario_portfolio_drain`: Run backtest with small capital to verify bot stops trading and exits gracefully before balance goes negative due to fees.

## Verification Method
- Ensure `tests/e2e/test_e2e.py` contains exactly the 29 test case functions outlined above.
- Run `pytest tests/e2e/test_e2e.py --collect-only` to verify all tests are discovered.
- Once the CLI tools are implemented, `pytest tests/e2e/` must pass completely.
