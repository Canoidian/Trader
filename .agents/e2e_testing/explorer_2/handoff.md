# Handoff: E2E Test Strategy & Test Cases

## Observation
I analyzed the testing requirements from the following files:
1. `TEST_INFRA.md`: Specifies opaque-box testing using `pytest`, invoking `scripts/run_backtest.py` and `scripts/run_analysis.py` via `subprocess`. Requires 4 tiers of testing: Category-Partition (Tier 1), BVA (Tier 2), Pairwise (Tier 3), and Real-World Scenarios (Tier 4) with coverage thresholds.
2. `ORIGINAL_REQUEST.md`: Details the Acceptance Criteria (AC).
   - **Feature 1 (Backtest)**: Simulates ≥10 trades, explicitly subtracts Kraken fees, and outputs a final PnL summary.
   - **Feature 2 (Analysis)**: Evaluates ≥3 coins, outputs ranked recommendations, and runs completely locally without high resource requirements.

## Logic Chain
Since these are opaque-box tests for CLI scripts that do not yet exist, we must design tests based purely on observable outputs (stdout/stderr) and exit codes. We assume the scripts will either support basic CLI arguments (like `--trades`, `--coins`) or their default execution will meet the boundaries necessary for testing.

1. **Tier 1 (Category-Partition)** focuses on normal execution paths, validating that default behaviors satisfy the core AC (10+ trades, 3+ coins, PnL output, ranked output).
2. **Tier 2 (Boundary Value Analysis)** targets edge cases around the AC thresholds: 0 trades, 1 trade, 9 trades, 10 trades, 0 coins, 1 coin, 2 coins, 3 coins.
3. **Tier 3 (Pairwise)** focuses on the interaction between the two scripts. Since they are separate CLIs, interaction is modeled by piping or passing the output of `run_analysis.py` as an input to `run_backtest.py`.
4. **Tier 4 (Scenarios)** models real-world workflows the user will perform, combining analysis, backtesting, and performance under stress or error conditions.

## Caveats
- **CLI Interface Assumptions**: The exact arguments (e.g., `--trades`, `--coins`) are hypothetical. Once the implementer designs the CLI, the test cases may need minor adjustments to match the actual argument flags.
- **Mocking**: Testing certain boundaries (like exactly 9 trades or API failures) might require mock data or offline mode flags in the implementation. If the CLI only uses hardcoded live data, some of these tests will need to rely on specific test fixtures.

## Conclusion

The following `pytest` test cases should be implemented in `tests/e2e/test_e2e.py`:

### Tier 1: Category-Partition (Equivalence Partitioning)
*Feature 1: Execution & Fee Verification*
1. `test_t1_f1_default_backtest_meets_ac`: Run `run_backtest.py` with no args. Verify exit code 0, ≥10 trades simulated, and "PnL" and "Fee" in stdout.
2. `test_t1_f1_custom_trade_count`: Run `run_backtest.py --trades 15`. Verify exactly 15 trades are executed and summarized.
3. `test_t1_f1_profitable_scenario`: Run backtest with a known profitable historical dataset. Verify (Gross PnL - Fees) equals Net PnL.
4. `test_t1_f1_unprofitable_scenario`: Run backtest with a known unprofitable dataset. Verify fees correctly compound the losses.
5. `test_t1_f1_invalid_arguments`: Run `run_backtest.py --invalid-arg`. Verify non-zero exit code and appropriate error message.

*Feature 2: Research Verification*
6. `test_t1_f2_default_analysis_meets_ac`: Run `run_analysis.py` with no args. Verify exit code 0, ≥3 coins evaluated, and output contains rankings (e.g., "Rank 1", "Rank 2").
7. `test_t1_f2_specific_coins`: Run `run_analysis.py --coins BTC ETH ADA`. Verify exactly these 3 coins are evaluated and ranked.
8. `test_t1_f2_large_coin_set`: Run analysis on 10 coins. Verify ranking logic holds and output format remains correct.
9. `test_t1_f2_network_timeout`: Run with a simulated network block (or invalid API endpoint). Verify it fails gracefully rather than crashing with an unhandled exception.
10. `test_t1_f2_output_format`: Verify stdout contains required columns/headers (Coin, Score/Rank, Recommendation).

### Tier 2: Boundary Value Analysis (BVA)
*Feature 1: Backtest Boundaries*
11. `test_t2_f1_zero_trades`: Run `run_backtest.py --trades 0`. Verify 0 fees and 0 PnL.
12. `test_t2_f1_one_trade`: Run `run_backtest.py --trades 1`. Verify single-trade fee logic.
13. `test_t2_f1_nine_trades`: Run `run_backtest.py --trades 9`. Verify execution, but note it's just below the AC requirement of 10.
14. `test_t2_f1_ten_trades`: Run `run_backtest.py --trades 10`. Verify exact AC boundary compliance.
15. `test_t2_f1_dust_limit_trades`: Run backtest with minimal initial balance. Verify fee calculation handles fractional pennies correctly.

*Feature 2: Analysis Boundaries*
16. `test_t2_f2_zero_coins`: Run `run_analysis.py --coins ""`. Verify it rejects the input or safely exits.
17. `test_t2_f2_one_coin`: Run `run_analysis.py --coins BTC`. Verify it handles a lack of comparison candidates gracefully.
18. `test_t2_f2_two_coins`: Run `run_analysis.py --coins BTC ETH`. Verify ranking of exactly 2 items.
19. `test_t2_f2_three_coins`: Run `run_analysis.py --coins BTC ETH ADA`. Verify exact AC boundary compliance.
20. `test_t2_f2_performance_limit`: Run default analysis and assert execution time is under a reasonable threshold (e.g., < 30 seconds) to satisfy "computationally efficient".

### Tier 3: Pairwise Interactions
21. `test_t3_p1_analysis_to_backtest`: Run analysis, parse stdout for Rank 1 coin, then run backtest on that specific coin. Verify both succeed.
22. `test_t3_p2_analysis_fail_backtest_default`: Simulate analysis failure, verify backtest can still run independently on a default fallback.
23. `test_t3_p3_analysis_obscure_coin`: Analysis recommends a coin with no historical data; pass to backtest. Verify backtest handles missing data gracefully.
24. `test_t3_p4_high_volatility_pair`: Analysis identifies high volatility; backtest confirms many trades are triggered, accumulating high fees.
25. `test_t3_p5_stablecoin_pair`: Analysis identifies a stablecoin (low volatility); backtest confirms few trades and minimal fee erosion.

### Tier 4: Real-World Application Scenarios
26. `test_t4_s1_full_automated_pipeline`: The primary E2E scenario. Run analysis, extract top recommendation, run backtest on it with real Kraken fee structures, verify final PnL output.
27. `test_t4_s2_multi_coin_comparison`: Extract top 3 coins from analysis, run 3 separate backtests, compare output PnLs to see if the highest ranked coin actually yielded the best backtested PnL.
28. `test_t4_s3_bear_market_survival`: Run the pipeline on historical data from a known crash period. Verify fee erosion is accurately represented and the system doesn't generate invalid trades.
29. `test_t4_s4_high_frequency_fee_drain`: Force the backtest to execute 100+ small volatile trades. Verify that the sum of fees is properly deducted and highlighted as a primary factor in the Net PnL.
30. `test_t4_s5_system_stress_recovery`: Run analysis with concurrent background CPU load (stressing the "older Mac Mini" constraint), then run backtest with corrupted config. Verify clear error messages and successful execution when config is corrected.

## Verification Method
1. The implementer should create the `tests/e2e/test_e2e.py` file based on these definitions.
2. Run `pytest tests/e2e/test_e2e.py --collect-only` to verify all 30 tests are recognized.
3. Once the CLI scripts are implemented, run `pytest tests/e2e/test_e2e.py -v` to ensure they pass and stdout parsing correctly validates the acceptance criteria.
