# Trading Bot Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 4-feature Random Forest with a 22-feature LightGBM model, add market regime detection, and confidence-weighted position sizing to improve buy signal quality.

**Architecture:** New indicators are pure functions added to `analysis.py`. The model trainer (`ml_trainer.py`) is rewritten to use LightGBM with walk-forward cross-validation. A new `regime.py` module classifies market state (BULL/BEAR/SIDEWAYS) from BTC/USD and returns a dynamic buy threshold. The live loop in `run_live.py` uses the regime threshold, samples 30 pairs (up from 10), and sizes positions by model confidence score.

**Tech Stack:** Python 3, LightGBM, scikit-learn (TimeSeriesSplit), joblib, Kraken REST API

---

## Task 1: Extend API — Multi-Interval OHLCV

**Files:**
- Modify: `krakentrader/api.py` (after line 44)

The existing `get_historical_ohlcv(pair)` hardcodes interval=1. We need a parameterized version for 5-min and 15-min candles.

- [ ] **Step 1: Add `get_historical_ohlcv_interval` to `krakentrader/api.py`**

Insert after line 44 (after the closing `return []` of `get_historical_ohlcv`):

```python
def get_historical_ohlcv_interval(pair, interval=1):
    """
    Fetch historical OHLC data at a specific interval (in minutes).
    interval: 1, 5, 15, 30, 60, 240, 1440
    Returns list of [time, open, high, low, close, vwap, volume, count].
    """
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"

    for attempt in range(3):
        response = requests.get(url)
        if response.status_code == 429:
            time.sleep(1 * (2 ** attempt))
            continue
        response.raise_for_status()
        data = response.json()
        if any("Rate limit" in str(err) for err in data.get('error', [])):
            time.sleep(1 * (2 ** attempt))
            continue
        break
    else:
        raise Exception("Kraken API rate limit exceeded after 3 attempts.")

    if data.get('error'):
        raise Exception(f"Kraken API error: {data['error']}")

    for key in data['result'].keys():
        if key != 'last':
            return data['result'][key]

    return []
```

- [ ] **Step 2: Verify the function exists**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -c "from krakentrader.api import get_historical_ohlcv_interval; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add krakentrader/api.py
git commit -m "feat: add get_historical_ohlcv_interval for multi-timeframe data"
```

---

## Task 2: New Indicator Functions — Trend & Volatility

**Files:**
- Modify: `krakentrader/analysis.py`
- Modify: `tests/test_analysis.py`

Add EMA, MACD, Bollinger Bands, ATR. All pure functions, no external dependencies.

- [ ] **Step 1: Write failing tests in `tests/test_analysis.py`**

Add after the existing `test_calculate_composite_score` function:

```python
from krakentrader.analysis import (
    calculate_ema, calculate_macd,
    calculate_bollinger_bands, calculate_bb_pct_b, calculate_bb_width,
    calculate_atr
)

def test_calculate_ema():
    closes = [10.0] * 5
    assert calculate_ema(closes, 5) == 10.0
    # Period > len
    assert calculate_ema([10.0, 11.0], 5) is None
    # Period <= 0
    assert calculate_ema([10.0, 11.0, 12.0], 0) is None
    # EMA in uptrend is above simple midpoint
    closes_up = [10.0 + i for i in range(20)]
    ema = calculate_ema(closes_up, 10)
    assert ema is not None
    assert ema > 14.0  # last value is 29, EMA lags but well above midpoint

def test_calculate_macd():
    # Too short — need >= 35 bars
    assert calculate_macd([10.0] * 20) == (None, None, None)
    # Uptrend: MACD line > 0 (fast EMA > slow EMA)
    closes_up = [10.0 + i * 0.2 for i in range(40)]
    macd_line, signal, histogram = calculate_macd(closes_up)
    assert macd_line is not None
    assert signal is not None
    assert histogram is not None
    assert macd_line > 0

def test_calculate_bollinger_bands():
    # Flat data: bands collapse to middle
    closes = [10.0] * 25
    upper, middle, lower = calculate_bollinger_bands(closes)
    assert upper == middle == lower == 10.0
    # Too short
    assert calculate_bollinger_bands([10.0] * 10) == (None, None, None)
    # With variance: upper > middle > lower
    import random as rnd; rnd.seed(42)
    closes_var = [10.0 + rnd.gauss(0, 0.5) for _ in range(25)]
    u, m, l = calculate_bollinger_bands(closes_var)
    assert u > m > l

def test_calculate_bb_pct_b():
    # At lower band: %B = 0, at upper band: %B = 1
    closes_flat = [10.0] * 25  # zero-width bands → return 0.5
    assert calculate_bb_pct_b(closes_flat) == 0.5
    # Too short
    assert calculate_bb_pct_b([10.0] * 10) is None

def test_calculate_bb_width():
    # Flat: width = 0
    assert calculate_bb_width([10.0] * 25) == 0.0
    # Too short
    assert calculate_bb_width([10.0] * 10) is None

def test_calculate_atr():
    # Constant candles: TR = high - low = 2, ATR = 2, normalized = 2/10 = 0.2
    highs = [11.0] * 20
    lows = [9.0] * 20
    closes = [10.0] * 20
    atr = calculate_atr(highs, lows, closes, period=14)
    assert atr is not None
    assert abs(atr - 0.2) < 0.01
    # Too short
    assert calculate_atr([11.0]*5, [9.0]*5, [10.0]*5, period=14) is None
```

- [ ] **Step 2: Run tests — expect ImportError (functions don't exist yet)**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_analysis.py -v -k "ema or macd or bollinger or bb_pct or bb_width or atr" 2>&1 | head -40
```

Expected: `ImportError` or `FAILED` — functions not yet defined.

- [ ] **Step 3: Add indicator functions to `krakentrader/analysis.py`**

Insert after the `calculate_volatility` function (after line 71), before `calculate_composite_score`:

```python
def calculate_ema(closes, period):
    if period <= 0 or len(closes) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calculate_macd(closes):
    if len(closes) < 35:
        return None, None, None
    k12 = 2.0 / 13
    k26 = 2.0 / 27
    k9 = 2.0 / 10
    ema12 = sum(closes[:12]) / 12
    ema26 = sum(closes[:26]) / 26
    for price in closes[12:26]:
        ema12 = price * k12 + ema12 * (1 - k12)
    macd_series = []
    for price in closes[26:]:
        ema12 = price * k12 + ema12 * (1 - k12)
        ema26 = price * k26 + ema26 * (1 - k26)
        macd_series.append(ema12 - ema26)
    if len(macd_series) < 9:
        return None, None, None
    signal = sum(macd_series[:9]) / 9
    for m in macd_series[9:]:
        signal = m * k9 + signal * (1 - k9)
    macd_line = macd_series[-1]
    return macd_line, signal, macd_line - signal

def calculate_bollinger_bands(closes, period=20, num_std=2):
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    std = variance ** 0.5
    return middle + num_std * std, middle, middle - num_std * std

def calculate_bb_pct_b(closes, period=20):
    result = calculate_bollinger_bands(closes, period)
    if result == (None, None, None):
        return None
    upper, middle, lower = result
    band_width = upper - lower
    if band_width == 0:
        return 0.5
    return (closes[-1] - lower) / band_width

def calculate_bb_width(closes, period=20):
    result = calculate_bollinger_bands(closes, period)
    if result == (None, None, None):
        return None
    upper, middle, lower = result
    if middle == 0:
        return 0.0
    return (upper - lower) / middle

def calculate_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return None
    true_ranges = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        true_ranges.append(tr)
    if len(true_ranges) < period:
        return None
    atr = sum(true_ranges[-period:]) / period
    if closes[-1] == 0:
        return 0.0
    return atr / closes[-1]
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_analysis.py -v -k "ema or macd or bollinger or bb_pct or bb_width or atr"
```

Expected: 6 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add krakentrader/analysis.py tests/test_analysis.py
git commit -m "feat: add EMA, MACD, Bollinger Bands, ATR indicator functions"
```

---

## Task 3: New Indicator Functions — Momentum & Volume

**Files:**
- Modify: `krakentrader/analysis.py`
- Modify: `tests/test_analysis.py`

Add Stochastic RSI, Williams %R, ROC, OBV slope, VWAP diff, volume ratio.

- [ ] **Step 1: Write failing tests in `tests/test_analysis.py`**

Add after the `test_calculate_atr` function:

```python
from krakentrader.analysis import (
    calculate_stoch_rsi, calculate_williams_r, calculate_roc,
    calculate_obv_slope, calculate_vwap_diff, calculate_volume_ratio
)

def test_calculate_stoch_rsi():
    # Need at least 14*2+3 = 31 bars
    assert calculate_stoch_rsi([10.0] * 10) == (None, None)
    # Steady uptrend → RSI high → StochRSI K near 100
    closes_up = [10.0 + i * 0.1 for i in range(40)]
    k, d = calculate_stoch_rsi(closes_up)
    assert k is not None and d is not None
    assert 0.0 <= k <= 100.0
    assert 0.0 <= d <= 100.0

def test_calculate_williams_r():
    highs = [12.0] * 15
    lows = [8.0] * 15
    closes = [10.0] * 15
    # At midpoint: %R = (12-10)/(12-8)*-100 = -50
    wr = calculate_williams_r(highs, lows, closes)
    assert abs(wr - (-50.0)) < 0.001
    # Too short
    assert calculate_williams_r([12.0]*5, [8.0]*5, [10.0]*5, period=14) is None

def test_calculate_roc():
    # 10% increase over 5 bars
    closes = [10.0] * 5 + [11.0] * 6
    roc = calculate_roc(closes, period=5)
    assert abs(roc - 0.10) < 0.001
    # Too short
    assert calculate_roc([10.0] * 3, period=5) is None

def test_calculate_obv_slope():
    # Uptrend with volume: OBV increases → positive slope
    closes = [10.0 + i * 0.5 for i in range(12)]
    volumes = [100.0] * 12
    slope = calculate_obv_slope(closes, volumes, lookback=10)
    assert slope is not None
    assert slope > 0
    # Too short
    assert calculate_obv_slope([10.0]*3, [100.0]*3, lookback=10) is None

def test_calculate_vwap_diff():
    # Price = VWAP → diff = 0
    closes = [10.0] * 5
    vwaps = [10.0] * 5
    assert calculate_vwap_diff(closes, vwaps) == 0.0
    # Price 10% above VWAP
    assert abs(calculate_vwap_diff([11.0]*5, [10.0]*5) - 0.1) < 0.001

def test_calculate_volume_ratio():
    # Last bar is 2× average of prior 14 bars
    volumes = [100.0] * 14 + [200.0]
    ratio = calculate_volume_ratio(volumes)
    assert abs(ratio - 2.0) < 0.001
    # Too short
    assert calculate_volume_ratio([100.0] * 5) is None
```

- [ ] **Step 2: Run tests — expect ImportError (functions don't exist yet)**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_analysis.py -v -k "stoch or williams or roc or obv or vwap or volume_ratio" 2>&1 | head -20
```

Expected: `ImportError` or `FAILED`.

- [ ] **Step 3: Add momentum & volume functions to `krakentrader/analysis.py`**

Insert after `calculate_atr` (before `calculate_composite_score`):

```python
def _rsi_series(closes, period, count):
    """Compute last `count` RSI values for StochRSI."""
    result = []
    for i in range(count):
        end = len(closes) - (count - 1 - i)
        lookback_start = max(0, end - period * 4)
        r = calculate_rsi(closes[lookback_start:end], period)
        if r is not None:
            result.append(r)
    return result

def calculate_stoch_rsi(closes, period=14):
    """Returns (%K, %D). K = StochRSI*100, D = 3-bar avg of K."""
    if len(closes) < period * 2 + 3:
        return None, None
    rsi_vals = _rsi_series(closes, period, period + 3)
    if len(rsi_vals) < period + 3:
        return None, None
    k_vals = []
    for i in range(3):
        window = rsi_vals[i: i + period]
        lo, hi = min(window), max(window)
        curr = rsi_vals[i + period]
        if hi == lo:
            k_vals.append(50.0)
        else:
            k_vals.append((curr - lo) / (hi - lo) * 100.0)
    return k_vals[-1], sum(k_vals) / 3

def calculate_williams_r(highs, lows, closes, period=14):
    if len(closes) < period:
        return None
    h = max(highs[-period:])
    l = min(lows[-period:])
    if h == l:
        return -50.0
    return (h - closes[-1]) / (h - l) * -100.0

def calculate_roc(closes, period=10):
    if len(closes) < period + 1:
        return None
    prev = closes[-period - 1]
    if prev == 0:
        return 0.0
    return (closes[-1] - prev) / prev

def calculate_obv_slope(closes, volumes, lookback=10):
    if len(closes) < lookback + 1 or len(volumes) < lookback + 1:
        return None
    obv = 0.0
    obv_series = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv += volumes[i]
        elif closes[i] < closes[i - 1]:
            obv -= volumes[i]
        obv_series.append(obv)
    window = obv_series[-lookback:]
    n = len(window)
    return (window[-1] - window[0]) / (n - 1) if n > 1 else 0.0

def calculate_vwap_diff(closes, vwaps):
    if not closes or not vwaps:
        return 0.0
    vwap = vwaps[-1]
    if vwap == 0:
        return 0.0
    return (closes[-1] - vwap) / vwap

def calculate_volume_ratio(volumes, period=14):
    if len(volumes) < period + 1:
        return None
    avg = sum(volumes[-period - 1:-1]) / period
    if avg == 0:
        return 1.0
    return volumes[-1] / avg
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_analysis.py -v -k "stoch or williams or roc or obv or vwap or volume_ratio"
```

Expected: 6 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add krakentrader/analysis.py tests/test_analysis.py
git commit -m "feat: add StochRSI, Williams R, ROC, OBV slope, VWAP diff, volume ratio indicators"
```

---

## Task 4: Update `calculate_composite_score` to 22 Features

**Files:**
- Modify: `krakentrader/analysis.py` (the `calculate_composite_score` function)
- Modify: `tests/test_analysis.py`

Update the function to accept optional OHLCV components and build the 22-feature vector. The naive fallback is unchanged. Backward-compatible signature.

- [ ] **Step 1: Write a test for the new signature**

Add after `test_calculate_composite_score` in `tests/test_analysis.py`:

```python
def test_calculate_composite_score_with_ohlcv():
    # With all optional data, function should still return a float in [0, 100]
    # No model loaded in test env, so uses naive fallback — just verify signature works
    closes = [10.0 + i * 0.01 for i in range(60)]
    highs = [c + 0.05 for c in closes]
    lows = [c - 0.05 for c in closes]
    volumes = [1000.0] * 60
    vwaps = closes[:]

    score = calculate_composite_score(
        closes, highs=highs, lows=lows,
        volumes=volumes, vwaps=vwaps,
        closes_5m=closes[::5], closes_15m=closes[::15]
    )
    assert isinstance(score, float)

def test_calculate_composite_score_backward_compat():
    # Old call signature still works
    closes = [10.0] * 35
    score = calculate_composite_score(closes)
    assert isinstance(score, float)
```

- [ ] **Step 2: Run tests — expect PASS (naive fallback ignores new params)**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_analysis.py -v -k "composite_score_with_ohlcv or composite_score_backward"
```

Expected: 2 tests PASSED (naive fallback doesn't use new params yet, but signature accepted).

- [ ] **Step 3: Replace `calculate_composite_score` in `krakentrader/analysis.py`**

Replace the entire `calculate_composite_score` function (lines 73–125 in the original):

```python
def _safe(val, default=0.0):
    """Return val if not None, else default."""
    return val if val is not None else default

def calculate_composite_score(closes, highs=None, lows=None, volumes=None,
                               vwaps=None, closes_5m=None, closes_15m=None):
    """
    Returns a composite score 0–100. Higher = stronger buy signal.
    If ML model loaded, uses 22-feature LightGBM score.
    Falls back to naive heuristic if no model.
    """
    if len(closes) < 31:
        return 0.0

    model = load_model()
    if model is not None:
        current_price = closes[-1]

        # --- Trend ---
        sma_14 = calculate_sma(closes[-14:], 14)
        sma_30 = calculate_sma(closes[-30:], 30)
        ema_21 = calculate_ema(closes, 21) if len(closes) >= 21 else None
        ema_50 = calculate_ema(closes, 50) if len(closes) >= 50 else calculate_ema(closes, len(closes))
        sma14_diff = (current_price - sma_14) / sma_14 if sma_14 else 0.0
        sma30_diff = (current_price - sma_30) / sma_30 if sma_30 else 0.0
        ema21_diff = (current_price - ema_21) / ema_21 if ema_21 else 0.0
        ema50_diff = (current_price - ema_50) / ema_50 if ema_50 else 0.0

        macd_line, macd_sig, macd_hist = calculate_macd(closes) if len(closes) >= 35 else (0.0, 0.0, 0.0)

        # --- Volatility / Bands ---
        bb_b = _safe(calculate_bb_pct_b(closes), 0.5)
        bb_w = _safe(calculate_bb_width(closes), 0.0)
        atr_norm = _safe(calculate_atr(highs, lows, closes) if highs and lows else None, 0.0)
        volat = calculate_volatility(closes[-14:])

        # --- Momentum ---
        rsi14 = _safe(calculate_rsi(closes[-28:], 14), 50.0)
        stoch_k, stoch_d = calculate_stoch_rsi(closes)
        stoch_k = _safe(stoch_k, 50.0)
        stoch_d = _safe(stoch_d, 50.0)
        willi = _safe(calculate_williams_r(highs, lows, closes) if highs and lows else None, -50.0)
        roc10 = _safe(calculate_roc(closes, 10), 0.0)

        # --- Volume ---
        obv_sl = _safe(calculate_obv_slope(closes, volumes) if volumes else None, 0.0)
        vwap_d = calculate_vwap_diff(closes, vwaps) if vwaps else 0.0
        vol_r = _safe(calculate_volume_ratio(volumes) if volumes else None, 1.0)

        # --- Multi-timeframe ---
        rsi_5m = 50.0
        sma20_diff_5m = 0.0
        if closes_5m and len(closes_5m) >= 20:
            rsi_5m = _safe(calculate_rsi(closes_5m[-28:], 14) if len(closes_5m) >= 28 else None, 50.0)
            sma20_5m = calculate_sma(closes_5m[-20:], 20)
            if sma20_5m:
                sma20_diff_5m = (closes_5m[-1] - sma20_5m) / sma20_5m

        rsi_15m = 50.0
        if closes_15m and len(closes_15m) >= 28:
            rsi_15m = _safe(calculate_rsi(closes_15m[-28:], 14), 50.0)

        features = [[
            sma14_diff, sma30_diff, ema21_diff, ema50_diff,
            rsi14, stoch_k, stoch_d, willi, roc10,
            _safe(macd_line, 0.0), _safe(macd_sig, 0.0), _safe(macd_hist, 0.0),
            bb_b, bb_w, atr_norm,
            obv_sl, vwap_d, vol_r,
            volat,
            rsi_5m, sma20_diff_5m, rsi_15m
        ]]

        prob = model.predict_proba(features)[0][1]
        return prob * 100.0

    # --- Fallback: Naive Heuristic ---
    sma14 = calculate_sma(closes, 14)
    rsi14 = calculate_rsi(closes, 14)
    volatility = calculate_volatility(closes)

    current_price = closes[-1]
    score = 0.0

    if sma14 is not None and current_price > sma14:
        score += 5.0
    else:
        score -= 5.0

    if rsi14 is not None:
        if rsi14 < 30:
            score += 10.0
        elif rsi14 > 70:
            score -= 10.0
        else:
            score += 10.0 - ((rsi14 - 30) / 40.0) * 20.0

    score -= volatility * 100.0
    return score
```

- [ ] **Step 4: Run all analysis tests**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_analysis.py -v
```

Expected: All tests PASS (all 12+ tests).

- [ ] **Step 5: Commit**

```bash
git add krakentrader/analysis.py tests/test_analysis.py
git commit -m "feat: update composite_score to 22-feature ML path with optional OHLCV params"
```

---

## Task 5: LightGBM Trainer with Walk-Forward CV

**Files:**
- Modify: `krakentrader/ml_trainer.py`
- Modify: `requirements.txt`

Replace `RandomForestClassifier` with LightGBM. Use walk-forward CV. Extract 22 features per training sample using resampled multi-timeframe data.

- [ ] **Step 1: Update `requirements.txt`**

Replace the file content:

```
requests
python-dotenv
scikit-learn
joblib
numpy
lightgbm
```

- [ ] **Step 2: Install new dependencies**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && pip install lightgbm numpy
```

Expected: `Successfully installed lightgbm-...`

- [ ] **Step 3: Replace `krakentrader/ml_trainer.py` entirely**

```python
import os
import sys
import time
import logging
import random
import joblib
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import precision_score, recall_score, f1_score
import lightgbm as lgb

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from krakentrader.api import get_tradable_pairs, get_historical_ohlcv
from krakentrader.analysis import (
    calculate_sma, calculate_rsi, calculate_volatility,
    calculate_ema, calculate_macd, calculate_bb_pct_b, calculate_bb_width,
    calculate_atr, calculate_stoch_rsi, calculate_williams_r, calculate_roc,
    calculate_obv_slope, calculate_vwap_diff, calculate_volume_ratio,
    _safe
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'model.pkl')

FEATURE_NAMES = [
    'sma14_diff', 'sma30_diff', 'ema21_diff', 'ema50_diff',
    'rsi14', 'stoch_k', 'stoch_d', 'williams_r', 'roc10',
    'macd_line', 'macd_signal', 'macd_hist',
    'bb_pct_b', 'bb_width', 'atr_norm',
    'obv_slope', 'vwap_diff', 'volume_ratio',
    'volatility',
    'rsi_5m', 'sma20_diff_5m', 'rsi_15m'
]

def _extract_features(closes, highs, lows, volumes, vwaps, i, min_bars=150):
    """Extract 22 features at index i. Returns list or None."""
    if i < min_bars:
        return None

    c = closes[:i + 1]
    h = highs[:i + 1]
    l = lows[:i + 1]
    v = volumes[:i + 1]
    vw = vwaps[:i + 1]

    current_price = c[-1]

    sma_14 = calculate_sma(c[-14:], 14)
    sma_30 = calculate_sma(c[-30:], 30)
    ema_21 = calculate_ema(c, 21)
    ema_50 = calculate_ema(c, 50) if len(c) >= 50 else calculate_ema(c, len(c))

    sma14_diff = (current_price - sma_14) / sma_14 if sma_14 else 0.0
    sma30_diff = (current_price - sma_30) / sma_30 if sma_30 else 0.0
    ema21_diff = (current_price - ema_21) / ema_21 if ema_21 else 0.0
    ema50_diff = (current_price - ema_50) / ema_50 if ema_50 else 0.0

    macd_line, macd_sig, macd_hist = calculate_macd(c) if len(c) >= 35 else (0.0, 0.0, 0.0)

    bb_b = _safe(calculate_bb_pct_b(c), 0.5)
    bb_w = _safe(calculate_bb_width(c), 0.0)
    atr_norm = _safe(calculate_atr(h, l, c), 0.0)
    volat = calculate_volatility(c[-14:])

    rsi14 = _safe(calculate_rsi(c[-28:], 14), 50.0)
    sk, sd = calculate_stoch_rsi(c)
    stoch_k = _safe(sk, 50.0)
    stoch_d = _safe(sd, 50.0)
    willi = _safe(calculate_williams_r(h, l, c), -50.0)
    roc10 = _safe(calculate_roc(c, 10), 0.0)

    obv_sl = _safe(calculate_obv_slope(c, v), 0.0)
    vwap_d = calculate_vwap_diff(c, vw)
    vol_r = _safe(calculate_volume_ratio(v), 1.0)

    # Multi-timeframe: resample 1-min to approximate 5-min and 15-min
    c5 = c[::5]
    c15 = c[::15]
    rsi_5m = _safe(calculate_rsi(c5[-28:], 14) if len(c5) >= 28 else None, 50.0)
    sma20_diff_5m = 0.0
    if len(c5) >= 20:
        sma20_5m = calculate_sma(c5[-20:], 20)
        if sma20_5m:
            sma20_diff_5m = (c5[-1] - sma20_5m) / sma20_5m
    rsi_15m = _safe(calculate_rsi(c15[-28:], 14) if len(c15) >= 28 else None, 50.0)

    return [
        sma14_diff, sma30_diff, ema21_diff, ema50_diff,
        rsi14, stoch_k, stoch_d, willi, roc10,
        _safe(macd_line, 0.0), _safe(macd_sig, 0.0), _safe(macd_hist, 0.0),
        bb_b, bb_w, atr_norm,
        obv_sl, vwap_d, vol_r,
        volat,
        rsi_5m, sma20_diff_5m, rsi_15m
    ]


def create_dataset():
    all_pairs = list(get_tradable_pairs(['ZUSD', 'USD']).keys())
    sample_pairs = random.sample(all_pairs, min(40, len(all_pairs)))

    X, y = [], []
    logging.info(f"Downloading data for {len(sample_pairs)} pairs...")

    for pair in sample_pairs:
        try:
            ohlcv = get_historical_ohlcv(pair)
            if not ohlcv or len(ohlcv) < 160:
                continue

            closes = [float(r[4]) for r in ohlcv]
            highs = [float(r[2]) for r in ohlcv]
            lows = [float(r[3]) for r in ohlcv]
            vwaps = [float(r[5]) for r in ohlcv]
            volumes = [float(r[6]) for r in ohlcv]

            for i in range(150, len(closes) - 10):
                future = closes[i + 1:i + 11]
                label = 1 if max(future) > closes[i] * 1.015 else 0

                feats = _extract_features(closes, highs, lows, volumes, vwaps, i)
                if feats is None:
                    continue

                X.append(feats)
                y.append(label)

            time.sleep(0.1)  # avoid rate limits
        except Exception as e:
            logging.error(f"Error processing {pair}: {e}")

    return np.array(X), np.array(y)


def train_model():
    X, y = create_dataset()
    if len(X) < 100:
        logging.error("Not enough data to train model.")
        return

    logging.info(f"Training LightGBM on {len(X)} samples. Positive: {sum(y)} ({100*sum(y)/len(y):.1f}%)")

    tscv = TimeSeriesSplit(n_splits=5)
    fold_scores = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        clf = lgb.LGBMClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            class_weight='balanced',
            random_state=42,
            verbose=-1
        )
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_val)
        p = precision_score(y_val, preds, zero_division=0)
        r = recall_score(y_val, preds, zero_division=0)
        f = f1_score(y_val, preds, zero_division=0)
        acc = clf.score(X_val, y_val)
        logging.info(f"Fold {fold+1}: Acc={acc*100:.1f}% Prec={p:.3f} Rec={r:.3f} F1={f:.3f}")
        fold_scores.append(f)

    logging.info(f"Mean F1: {np.mean(fold_scores):.3f}")

    # Train final model on all data
    final_clf = lgb.LGBMClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        num_leaves=31, class_weight='balanced', random_state=42, verbose=-1
    )
    final_clf.fit(X, y)

    # Feature importance
    importances = sorted(zip(FEATURE_NAMES, final_clf.feature_importances_), key=lambda x: -x[1])
    logging.info("Top 10 features:")
    for name, imp in importances[:10]:
        logging.info(f"  {name}: {imp}")

    joblib.dump(final_clf, MODEL_PATH)
    logging.info(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
```

- [ ] **Step 4: Verify the trainer imports correctly**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -c "from krakentrader.ml_trainer import create_dataset, train_model; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add krakentrader/ml_trainer.py requirements.txt
git commit -m "feat: replace Random Forest with LightGBM, walk-forward CV, 22-feature training"
```

---

## Task 6: Market Regime Detection Module

**Files:**
- Create: `krakentrader/regime.py`
- Modify: `tests/test_regime.py` (new file)

New module: classify BTC/USD market as BULL/BEAR/SIDEWAYS using ADX(14) + SMA(200). Result cached 10 minutes.

- [ ] **Step 1: Write failing tests**

Create `tests/test_regime.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from krakentrader.regime import calculate_adx, classify_regime, get_market_regime

def test_calculate_adx_trending():
    # Strong uptrend: price rises consistently
    n = 50
    closes = [100.0 + i * 0.5 for i in range(n)]
    highs = [c + 0.3 for c in closes]
    lows = [c - 0.3 for c in closes]
    adx = calculate_adx(highs, lows, closes)
    assert adx is not None
    assert adx > 0

def test_calculate_adx_too_short():
    assert calculate_adx([11.0]*5, [9.0]*5, [10.0]*5) is None

def test_classify_regime_bull():
    # ADX >= 20, price above SMA200
    regime, threshold = classify_regime(adx=25.0, price=110.0, sma200=100.0)
    assert regime == 'BULL'
    assert threshold == 60.0

def test_classify_regime_bear():
    regime, threshold = classify_regime(adx=25.0, price=90.0, sma200=100.0)
    assert regime == 'BEAR'
    assert threshold == 78.0

def test_classify_regime_sideways():
    regime, threshold = classify_regime(adx=15.0, price=100.0, sma200=100.0)
    assert regime == 'SIDEWAYS'
    assert threshold == 65.0

def test_get_market_regime_uses_cache():
    import krakentrader.regime as regime_module
    regime_module._regime_cache = None  # reset between tests
    regime_module._regime_cache_time = 0.0

    mock_api = MagicMock()
    ohlcv = [[i, 10.0, 10.3, 9.7, 10.0 + i*0.01, 10.0, 1000.0, 10] for i in range(300)]
    mock_api.get_historical_ohlcv_interval.return_value = ohlcv

    regime1, t1 = get_market_regime(mock_api)
    regime2, t2 = get_market_regime(mock_api)

    # Second call uses cache — API called exactly once
    assert mock_api.get_historical_ohlcv_interval.call_count == 1
    assert regime1 == regime2
    assert t1 == t2
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_regime.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name...`

- [ ] **Step 3: Create `krakentrader/regime.py`**

```python
import time
import logging

_regime_cache = None
_regime_cache_time = 0.0
_CACHE_TTL = 600  # 10 minutes


def calculate_adx(highs, lows, closes, period=14):
    """Average Directional Index. Returns None if insufficient data."""
    if len(closes) < period * 2 + 1:
        return None

    true_ranges, plus_dms, minus_dms = [], [], []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        true_ranges.append(tr)

        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dms.append(up if up > down and up > 0 else 0.0)
        minus_dms.append(down if down > up and down > 0 else 0.0)

    if len(true_ranges) < period:
        return None

    # Wilder smoothing seed
    atr = sum(true_ranges[:period])
    plus_dm = sum(plus_dms[:period])
    minus_dm = sum(minus_dms[:period])

    dx_series = []
    for i in range(period, len(true_ranges)):
        atr = atr - atr / period + true_ranges[i]
        plus_dm = plus_dm - plus_dm / period + plus_dms[i]
        minus_dm = minus_dm - minus_dm / period + minus_dms[i]

        if atr == 0:
            continue
        plus_di = 100.0 * plus_dm / atr
        minus_di = 100.0 * minus_dm / atr
        di_sum = plus_di + minus_di
        dx_series.append(100.0 * abs(plus_di - minus_di) / di_sum if di_sum else 0.0)

    if len(dx_series) < period:
        return None

    adx = sum(dx_series[:period]) / period
    for dx in dx_series[period:]:
        adx = (adx * (period - 1) + dx) / period

    return adx


def classify_regime(adx, price, sma200):
    """Return (regime_str, buy_threshold) from ADX and price vs SMA200."""
    if adx < 20:
        return 'SIDEWAYS', 65.0
    if price > sma200:
        return 'BULL', 60.0
    return 'BEAR', 78.0


def get_market_regime(api):
    """
    Returns (regime, buy_threshold) using BTC/USD as market proxy.
    Result cached 10 minutes to avoid excess API calls.
    """
    global _regime_cache, _regime_cache_time

    now = time.time()
    if _regime_cache is not None and (now - _regime_cache_time) < _CACHE_TTL:
        return _regime_cache

    try:
        ohlcv = api.get_historical_ohlcv_interval('XBTUSD', interval=1)
        if not ohlcv or len(ohlcv) < 210:
            return 'SIDEWAYS', 65.0

        closes = [float(r[4]) for r in ohlcv]
        highs = [float(r[2]) for r in ohlcv]
        lows = [float(r[3]) for r in ohlcv]

        adx = calculate_adx(highs, lows, closes)
        if adx is None:
            return 'SIDEWAYS', 65.0

        from krakentrader.analysis import calculate_sma
        sma200 = calculate_sma(closes, 200)
        if sma200 is None:
            return 'SIDEWAYS', 65.0

        regime, threshold = classify_regime(adx, closes[-1], sma200)
        logging.info(f"[REGIME] {regime} | ADX={adx:.1f} | Price={closes[-1]:.2f} | SMA200={sma200:.2f} | Threshold={threshold}%")

        _regime_cache = (regime, threshold)
        _regime_cache_time = now
        return _regime_cache

    except Exception as e:
        logging.error(f"Regime detection failed: {e}")
        return 'SIDEWAYS', 65.0
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/test_regime.py -v
```

Expected: 7 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add krakentrader/regime.py tests/test_regime.py
git commit -m "feat: add market regime detection (ADX + SMA200) with 10-min cache"
```

---

## Task 7: Live Loop Upgrades

**Files:**
- Modify: `scripts/run_live.py`

Three changes: (1) dynamic buy threshold from regime, (2) 30-pair sample instead of 10 random, (3) confidence-weighted position sizing, (4) pass full OHLCV data to composite_score.

- [ ] **Step 1: Read the current `run_live.py` to identify exact change points**

Lines to modify:
- Line 11 (imports): add `get_historical_ohlcv_interval`, `calculate_composite_score` stays, add regime import
- Lines 16–21 (constants): remove hardcoded threshold (now from regime), update sample size
- Lines 142–164 (market research): fetch multi-interval, pass to composite_score
- Line 166 (threshold): use `buy_threshold` from regime
- Line 169 (trade amount): use `confidence_to_fraction`

- [ ] **Step 2: Replace the import block at top of `scripts/run_live.py`**

Replace lines 1–13 with:

```python
import time
import logging
import random
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'state.json')

import krakentrader.api as _kraken_api
from krakentrader.api import (
    get_balance, create_order, get_historical_ohlcv,
    get_historical_ohlcv_interval, get_tradable_pairs, get_ticker
)
from krakentrader.analysis import calculate_composite_score
from krakentrader.regime import get_market_regime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```

- [ ] **Step 3: Replace constants block (lines 16–21)**

Replace:
```python
TRADE_FRACTION = 0.95    
MIN_TRADE_AMOUNT_USD = 5.0 
MAX_CONCURRENT_TRADES = 3
TRAILING_STOP_PCT = 0.03 # 3.0% trailing stop loss
MAX_HOLD_HOURS = 6.0     # Maximum hours to hold a trade
POLL_INTERVAL = 30       
```

With:
```python
MIN_TRADE_AMOUNT_USD = 5.0
MAX_CONCURRENT_TRADES = 3
TRAILING_STOP_PCT = 0.03
MAX_HOLD_HOURS = 6.0
POLL_INTERVAL = 30
SAMPLE_PAIRS = 30  # expanded from 10

def confidence_to_fraction(score: float) -> float:
    """Scale position size by model confidence."""
    if score >= 90:
        return 0.95
    if score >= 80:
        return 0.80
    if score >= 70:
        return 0.65
    return 0.40
```

- [ ] **Step 4: Update the market research section in `run_loop()`**

Replace lines 139–164 (the `# STEP 3: MARKET RESEARCH` block):

```python
                # STEP 3: MARKET RESEARCH
                if usable_assets:
                    # Detect market regime for dynamic threshold
                    regime, buy_threshold = get_market_regime(_kraken_api)

                    quote_currencies = [a['asset'] for a in usable_assets]
                    tradable_pairs_dict = get_tradable_pairs(quote_currencies)
                    all_pairs = list(tradable_pairs_dict.keys())

                    if all_pairs:
                        sample_pairs = random.sample(all_pairs, min(SAMPLE_PAIRS, len(all_pairs)))

                        best_pair = None
                        best_score = -9999
                        best_price = 0
                        best_quote_asset = None

                        for pair in sample_pairs:
                            try:
                                ohlcv = get_historical_ohlcv(pair)
                                if not ohlcv or len(ohlcv) < 35:
                                    continue
                                closes = [float(row[4]) for row in ohlcv]
                                highs = [float(row[2]) for row in ohlcv]
                                lows = [float(row[3]) for row in ohlcv]
                                volumes = [float(row[6]) for row in ohlcv]
                                vwaps = [float(row[5]) for row in ohlcv]

                                # Fetch multi-timeframe data
                                closes_5m, closes_15m = None, None
                                try:
                                    ohlcv_5m = get_historical_ohlcv_interval(pair, 5)
                                    closes_5m = [float(r[4]) for r in ohlcv_5m] if ohlcv_5m else None
                                except Exception:
                                    pass
                                try:
                                    ohlcv_15m = get_historical_ohlcv_interval(pair, 15)
                                    closes_15m = [float(r[4]) for r in ohlcv_15m] if ohlcv_15m else None
                                except Exception:
                                    pass

                                score = calculate_composite_score(
                                    closes, highs=highs, lows=lows,
                                    volumes=volumes, vwaps=vwaps,
                                    closes_5m=closes_5m, closes_15m=closes_15m
                                )
                                if score > best_score:
                                    best_score = score
                                    best_pair = pair
                                    best_price = closes[-1]
                                    best_quote_asset = tradable_pairs_dict[pair]

                                time.sleep(0.05)  # gentle rate limiting
                            except Exception:
                                pass
```

- [ ] **Step 5: Update the buy threshold check and position sizing (line 166–170)**

Replace:
```python
                        if best_score > 65.0 and best_quote_asset:
                            # STEP 4: BUY
                            asset_info = next(a for a in usable_assets if a['asset'] == best_quote_asset)
                            trade_amount = asset_info['amount'] * TRADE_FRACTION
```

With:
```python
                        if best_score > buy_threshold and best_quote_asset:
                            # STEP 4: BUY
                            asset_info = next(a for a in usable_assets if a['asset'] == best_quote_asset)
                            trade_fraction = confidence_to_fraction(best_score)
                            trade_amount = asset_info['amount'] * trade_fraction
```

- [ ] **Step 6: Update the BUY log line (line 172)**

Replace:
```python
                            logging.info(f"[BUY] ML Predicts {best_score:.1f}% pump probability! Using {trade_amount:.6f} {best_quote_asset} to buy {best_pair}")
```

With:
```python
                            logging.info(f"[BUY] {regime} regime | Score {best_score:.1f}% | Threshold {buy_threshold}% | Sizing {trade_fraction*100:.0f}% | Using {trade_amount:.6f} {best_quote_asset} to buy {best_pair}")
```

- [ ] **Step 7: Verify the live script imports without error**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -c "import scripts.run_live; print('OK')" 2>&1 || python -c "
import sys, os
sys.path.insert(0, '.')
exec(open('scripts/run_live.py').read().split('if __name__')[0])
print('OK')
"
```

Expected: `OK` (or no import errors)

- [ ] **Step 8: Commit**

```bash
git add scripts/run_live.py
git commit -m "feat: dynamic regime threshold, 30-pair sample, confidence-weighted sizing"
```

---

## Task 8: Run Full Test Suite & Fix Any Breaks

**Files:**
- Modify: `tests/test_analysis.py` if any tests break
- Modify: `tests/e2e/test_e2e.py` if any E2E tests break

- [ ] **Step 1: Run all tests**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/ -v 2>&1 | tail -40
```

- [ ] **Step 2: Fix any failing tests**

Common breaks:
- If E2E tests call `calculate_composite_score(closes)` — backward compatible, should pass
- If E2E tests import from `ml_trainer` and reference `RandomForestClassifier` — update references
- If any test patches `krakentrader.analysis.load_model` — these still work (function unchanged)

For each failing test, inspect the error and fix minimally. Do not rewrite passing tests.

- [ ] **Step 3: Confirm all 29 original E2E tests pass**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -m pytest tests/e2e/ -v 2>&1 | tail -20
```

Expected: 29 tests PASSED (plus new unit tests).

- [ ] **Step 4: Commit any test fixes**

```bash
git add tests/
git commit -m "fix: update tests for new composite_score signature and LightGBM trainer"
```

---

## Task 9: Train Model & Final Verification

- [ ] **Step 1: Train the LightGBM model**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python krakentrader/ml_trainer.py
```

Expected output includes:
- `Downloading data for 40 pairs...`
- `Fold 1: Acc=... Prec=... Rec=... F1=...` (5 folds)
- `Mean F1: ...`
- `Top 10 features:` (list of feature names with importances)
- `Model saved to .../model.pkl`

This takes 5–15 minutes (API calls + training).

- [ ] **Step 2: Verify model file exists**

```bash
ls -lh /Users/williamisaak/Projects/KrakenTraderV2/model.pkl
```

Expected: file exists, typically 1–10 MB.

- [ ] **Step 3: Smoke test the scoring pipeline**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -c "
from krakentrader.api import get_historical_ohlcv
from krakentrader.analysis import calculate_composite_score

ohlcv = get_historical_ohlcv('XBTUSD')
closes = [float(r[4]) for r in ohlcv]
highs = [float(r[2]) for r in ohlcv]
lows = [float(r[3]) for r in ohlcv]
volumes = [float(r[6]) for r in ohlcv]
vwaps = [float(r[5]) for r in ohlcv]
score = calculate_composite_score(closes, highs=highs, lows=lows, volumes=volumes, vwaps=vwaps)
print(f'BTC/USD score: {score:.2f}%')
"
```

Expected: prints a score between 0 and 100.

- [ ] **Step 4: Smoke test regime detection**

```bash
cd /Users/williamisaak/Projects/KrakenTraderV2 && python -c "
from krakentrader.api import get_historical_ohlcv_interval
from krakentrader.regime import get_market_regime

class Api:
    def get_historical_ohlcv_interval(self, pair, interval=1):
        return get_historical_ohlcv_interval(pair, interval)

regime, threshold = get_market_regime(Api())
print(f'Regime: {regime}, Threshold: {threshold}%')
"
```

Expected: prints `Regime: BULL` or `SIDEWAYS` or `BEAR` with threshold.

- [ ] **Step 5: Final commit**

```bash
git add model.pkl
git commit -m "feat: train LightGBM model with 22 features and walk-forward CV"
```

---

## Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| All tests pass | `pytest tests/ -v` | 35+ tests PASS |
| Model trains | `python krakentrader/ml_trainer.py` | Logs 5-fold CV + importances |
| Scoring works | smoke test in Task 9 Step 3 | Score 0–100 printed |
| Regime works | smoke test in Task 9 Step 4 | BULL/BEAR/SIDEWAYS printed |
| Live loop imports | `python -c "..."` from Task 7 Step 7 | No errors |
