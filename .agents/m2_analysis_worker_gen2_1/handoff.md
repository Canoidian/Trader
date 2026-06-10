# Observation
- Inspected `krakentrader/analysis.py` and `scripts/run_analysis.py` to identify the 5 requested bugs.
- Found the RSI scoring logic in `calculate_composite_score` had discontinuous transitions at RSI=30 (jump from 10 to 5) and RSI=70 (jump from -5 to -10).
- Found the truthiness check for SMA `if sma14 and current_price > sma14:` which would fail for an SMA of 0.
- Found `calculate_rsi` returns `100.0` when `avg_loss == 0` without checking if `avg_gain == 0` (flat asset).
- Found `run_analysis.py` had `len(closes) > 15`, excluding exactly 15 candles which the core logic supports.
- Found `urllib.request.urlopen(req)` lacked a timeout argument.

# Logic Chain
1. Updated `urllib.request.urlopen(req)` to `urllib.request.urlopen(req, timeout=10)` to prevent blocking indefinitely on network calls.
2. Changed `len(closes) > 15` to `len(closes) >= 15` in `run_analysis.py` to align with the core analysis requiring at least 15 candles.
3. In `calculate_rsi`, added an inner check `if avg_gain == 0:` to return `50.0` when both gain and loss are zero (perfectly flat asset), keeping `100.0` for pure gains.
4. Changed `if sma14 and current_price > sma14:` to `if sma14 is not None and current_price > sma14:` to prevent issues where SMA could legitimately be 0 but evaluate as falsey.
5. In `calculate_composite_score`, modified the RSI linear interpolation formula from `score += 5.0 - ((rsi14 - 30) / 40.0) * 10.0` to `score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0`. This ensures that at `rsi14=30`, the addition is `10.0` (matching the `< 30` condition), and at `rsi14=70`, the addition is `-10.0` (matching the `> 70` condition), completely fixing the discontinuous jumps.

# Caveats
- I avoided running the full `scripts/run_analysis.py` directly using `run_command` because the prompt specifically noted that `run_command` testing may time out waiting for user permission. The edits were implemented and verified through careful inspection instead.

# Conclusion
- All 5 specified bugs for the Milestone 2 Analysis Engine were fixed successfully by applying targeted code edits.

# Verification Method
- Review the `krakentrader/analysis.py` and `scripts/run_analysis.py` files to confirm the applied fixes.
- Run `python scripts/run_analysis.py` locally to verify that data fetches accurately (with timeouts) and that the analysis output includes correct calculations even for precisely 15 candles.
