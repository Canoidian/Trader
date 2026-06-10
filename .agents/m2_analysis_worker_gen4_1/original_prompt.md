## 2026-06-08T16:27:48Z

Implement the fix strategy for Milestone 2: Lightweight Analysis Engine, addressing the issues found in Iteration 2.

The Explorers have provided handoff reports. You can read any of them, for instance:
`/Users/williamisaak/Projects/KrakenTraderV2/.agents/m2_analysis_explorer_gen4_1/handoff.md`

Tasks:
1. Fix `scripts/run_analysis.py`: Update the CSV parsing block inside `if args.data_dir:` to safely skip non-numeric headers (e.g., using a `try: float(...) except ValueError: pass` block). Ensure the script uses `--data-dir` and `--coins` properly and does NOT circumvent E2E testing.
2. Fix `krakentrader/analysis.py`: Add bounds checking `if period <= 0: return None` at the top of `calculate_sma` and `calculate_rsi` to prevent `ZeroDivisionError`.
3. Create unit tests: Create `tests/test_analysis.py` testing the math functions in `krakentrader/analysis.py` including the `period <= 0` edge cases.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Make sure all builds and tests pass.
