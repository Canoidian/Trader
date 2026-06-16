# KrakenTraderV2 Upgrade — Design Spec

## Problem

Bot has been net-negative live. Root cause: weak buy signals (only 4 features, Random Forest, 10 random pairs sampled per loop, static 65% threshold regardless of market condition, single 1-minute timeframe). Priority: better buy signal quality (higher win rate, fewer bad entries).

## Approved Approach: Gradient Boosting + Regime Detection

### Feature Engineering (4 → 22 features)

| Category | Features |
|----------|----------|
| Trend (5) | SMA14 diff, SMA30 diff, EMA21 diff, EMA50 diff, MACD (line, signal, histogram) |
| Volatility/Bands (4) | Bollinger Band %B, BB width, ATR(14) normalized, existing volatility |
| Momentum (4) | Stochastic RSI %K and %D, Williams %R, Rate of Change(10) |
| Volume (3) | OBV slope (10-bar), VWAP deviation, volume ratio (current vs 14-bar avg) |
| Multi-timeframe (3) | RSI(14) on 5-min, SMA(20) diff on 5-min, RSI(14) on 15-min |

### Model: LightGBM replacing Random Forest

- `lgb.LGBMClassifier(n_estimators=500, max_depth=6, learning_rate=0.05, num_leaves=31, class_weight='balanced')`
- Walk-forward cross-validation (5 folds, time-series aware) — fixes data leakage bug in current random 80/20 split
- Logs per-fold Precision/Recall/F1 and top-10 feature importances

### Market Regime Detection (new `krakentrader/regime.py`)

Uses BTC/USD 1-min candles as market proxy. ADX(14) + SMA(200):
- ADX < 20 → **SIDEWAYS** → buy threshold 65%
- ADX ≥ 20 + price > SMA200 → **BULL** → buy threshold 60%
- ADX ≥ 20 + price < SMA200 → **BEAR** → buy threshold 78%
- Result cached 10 minutes

### Confidence-Weighted Position Sizing

Replaces flat 95%-of-balance with score-scaled sizing:
- score 60–70%: 40% of balance
- score 70–80%: 65% of balance
- score 80–90%: 80% of balance
- score ≥ 90%: 95% of balance

### Expanded Pair Sampling

Increases from 10 random pairs to 30 random pairs per loop. Full universe scan is impractical (200+ pairs × 3 API calls × 30s loop = too slow). 30 pairs gives 3× better market coverage.

## Files Changed

| File | Change |
|------|--------|
| `krakentrader/api.py` | Add `get_historical_ohlcv_interval(pair, interval)` |
| `krakentrader/analysis.py` | Add 12 new indicator functions; update `calculate_composite_score` signature |
| `krakentrader/ml_trainer.py` | Replace RF with LightGBM; walk-forward CV; 22 features; multi-timeframe resampling |
| `krakentrader/regime.py` | New: ADX + SMA200 regime classifier with 10-min cache |
| `scripts/run_live.py` | Regime-based threshold; 30-pair sample; confidence sizing; multi-interval data |
| `requirements.txt` | Add `lightgbm`, `numpy` (explicit) |
