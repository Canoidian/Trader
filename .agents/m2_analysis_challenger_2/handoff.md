# Handoff Report: Adversarial Challenge of M2 Lightweight Analysis Engine

## Observation
- Reviewed `krakentrader/analysis.py` and `scripts/run_analysis.py`.
- `calculate_sma(closes, period)` handles `len(closes) < period` by returning `None`, but does not guard against `period <= 0`.
- `calculate_rsi(closes, period=14)` implements Wilder's Smoothing correctly, maintaining accurate period indices. However, if price is completely flat (i.e. `avg_gain == 0` and `avg_loss == 0`), it defaults to returning `100.0`.
- `calculate_volatility(closes)` safely handles division by zero by checking `closes[i-1] == 0` and returning `0.0` for that day's return.
- `calculate_composite_score(closes)` checks `if sma14 and current_price > sma14:` to award points for an uptrend.
- `scripts/run_analysis.py` parses the Kraken API accurately, ignores the `'last'` key, extracts closing prices safely with float parsing, and catches missing keys or network failures using a blanket `except Exception`.

## Logic Chain
1. **RSI Flat-Line Edge Case**: In `calculate_rsi`, if a coin's price hasn't moved at all over the timeframe, both `avg_gain` and `avg_loss` evaluate to `0.0`. The script checks `if avg_loss == 0: return 100.0`. A flat asset is therefore assigned an RSI of `100.0` (maximally overbought). In `calculate_composite_score`, any RSI > 70 incurs a `-10.0` point penalty, which unfairly punishes a flat coin as if it were heavily overbought.
2. **SMA Falsy Edge Case**: In `calculate_composite_score`, the expression `if sma14 and current_price > sma14:` is intended to check if `sma14` is not `None`. However, if `sma14` is perfectly `0.0`, it evaluates to `False`. This causes the condition to fail even if `current_price` > `0.0`, unjustly penalizing the coin by subtracting `5.0` points.
3. **Missing Constraints in Math Functions**: `calculate_sma` will raise `ZeroDivisionError` if invoked with `period=0`, though statically it is currently only invoked with `period=14`.
4. **API Robustness**: The script gracefully falls back with `time.sleep(1)` to respect rate limits, and safely traps HTTP timeouts or unexpected JSON structures in a generic `except Exception` block, yielding `None` and skipping the malformed pair.

## Caveats
- Since the environment could not supply terminal user-approval for `run_command`, verification was conducted purely via static code analysis rather than dynamic stress testing.
- The highlighted edge cases (`sma14 == 0.0`, completely flat prices) are mathematically possible but very rare in real-world crypto data.

## Conclusion
**Verdict: PASS with Minor Vulnerabilities.**
The Milestone 2 engine strongly fulfills the architectural and scope requirements. It successfully ranks coins locally using lightweight standard libraries. The mathematical formulations are largely robust against runtime crashes, except for a logical falsy bug on `sma == 0.0` and a miscategorization of flat-lined RSIs as maximally overbought. Neither bug prevents standard execution on live, volatile crypto prices.

## Verification Method
1. Create a mock list of zero-priced data: `closes = [0.0] * 15`.
2. Run `calculate_sma(closes, 14)` to receive `0.0`.
3. Check `calculate_composite_score(closes)` step-by-step; notice `if sma14` evaluates to `False` (skipping the uptrend block) and `calculate_rsi` returns `100.0` (applying a `-10.0` penalty).
4. Inspect `scripts/run_analysis.py` to confirm `except Exception` effectively swallows failed URL retrievals.
