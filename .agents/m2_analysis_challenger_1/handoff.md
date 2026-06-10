# Handoff Report: Adversarial Challenge of M2 Lightweight Analysis Engine

## Observation
- Attempted to run dynamic stress tests using `run_command`, but encountered a permission timeout. Fallback to deep static analysis as per instructions.
- Reviewed `krakentrader/analysis.py` and `scripts/run_analysis.py` for mathematical flaws, edge cases, and API parsing logic.
- `calculate_composite_score` has an RSI penalty function:
  ```python
  if rsi14 < 30: score += 10.0
  elif rsi14 > 70: score -= 10.0
  else: score += 5.0 - ((rsi14 - 30) / 40.0) * 10.0
  ```
- `calculate_composite_score` uses a truthiness check for SMA: `if sma14 and current_price > sma14:`
- `calculate_rsi` handles zero division for `avg_loss == 0` by returning `100.0`.
- `run_analysis.py` checks `if closes and len(closes) > 15:` before proceeding, whereas `calculate_composite_score` in `analysis.py` checks `if len(closes) < 15:`.

## Logic Chain
1. **Discontinuous Scoring Function (Logic/Math Flaw)**: The RSI scoring creates a massive 5-point jump at the boundary. An RSI of `29.99` scores `+10.0`, but an RSI of `30.0` drops the score to `+5.0`. An RSI of `70.0` scores `-5.0`, but `70.01` drops it to `-10.0`. This will cause highly erratic ranking shifts for coins with near-identical technicals.
2. **Truthiness Bug (Logic Error)**: The condition `if sma14 and current_price > sma14:` fails if `sma14` is exactly `0.0`. Since `0.0` evaluates to `False` in Python, the code unfairly applies a trend penalty (`-5.0`) even if `current_price` is positive. The check must be `if sma14 is not None`.
3. **Flat Asset RSI Edge Case (Math Flaw)**: If an asset has perfectly flat price action, both `avg_gain` and `avg_loss` are `0.0`. The script hits `if avg_loss == 0: return 100.0`. This marks a completely dormant asset as "extremely overbought" instead of a neutral `50.0`.
4. **Inconsistent Data Requirements (Off-By-One)**: `run_analysis.py` strictly requires `> 15` (16 or more) candles. However, `analysis.py` requires `>= 15` candles (`if len(closes) < 15: return 0.0`). This inconsistency causes 15-candle datasets to be discarded silently by the runner.
5. **Zero Division Error Risk**: If `period=0` is passed to `calculate_sma` or `calculate_rsi`, both will raise a `ZeroDivisionError` because there is no guard against a period of zero.

## Caveats
- `run_command` timed out, so dynamic tests could not be executed. All vulnerabilities were discovered via static analysis.
- Some edge cases (like prices hitting exactly `0.0`) are rare in live crypto markets but must be handled properly in robust numerical software.

## Conclusion
**Verdict: FAIL**

The implementation is logically flawed. The 5-point discontinuity in the RSI scoring algorithm undermines its reliability as a ranking system. Furthermore, the `sma14 == 0.0` truthiness bug, the `RSI = 100.0` default for flat assets, and the off-by-one inconsistency in dataset length requirements must be fixed before this module can be trusted by the broader system.

## Verification Method
1. Call `calculate_composite_score` with a mocked dataset that produces an RSI of `29.99` versus `30.00` and observe the 5-point score drop.
2. Call `calculate_composite_score` with a dataset where `sma14 = 0.0` and `current_price = 1.0` and verify it incorrectly penalizes the score by `-5.0`.
3. Pass a flat array `[100.0]*20` to `calculate_rsi` and note it returns `100.0` instead of a neutral value.
