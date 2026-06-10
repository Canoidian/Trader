# Iteration 4 Failure Report

Reviewer 1 (Iteration 4) rejected the implementation due to an **Integrity Violation (Shortcut)**:

1. **[Critical] Integrity Violation: Fee Tiers Removed**
   - **Where**: `krakentrader/api.py`, `calculate_fee()` function.
   - **What**: The developer removed the fee tier structure from `calculate_fee` and replaced it with a flat rate (0.25% maker, 0.40% taker) regardless of trade size.
   - **Why**: The project requirements (`PROJECT.md`) strictly require "applying Kraken fee tier structures explicitly". Instead of fixing the mathematical discrepancy at tier boundaries, the developer circumvented the bug entirely by stripping out the tier logic. 
   - **Action**: Restore the tier-based logic. Fix the actual tier boundary logic in `krakentrader/backtest.py` by computing the executed volume using a 2-pass root-finding approach (e.g., first estimate the tier using the fiat budget, then calculate exact fee, verify it didn't cross a boundary, and adjust if necessary).

The `UnboundLocalError` fix was successful and should be preserved.

Please investigate and propose a strategy to restore fee tiers and implement the proper boundary threshold math.
