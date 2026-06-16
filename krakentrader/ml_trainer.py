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

            time.sleep(0.1)
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

    importances = sorted(zip(FEATURE_NAMES, final_clf.feature_importances_), key=lambda x: -x[1])
    logging.info("Top 10 features:")
    for name, imp in importances[:10]:
        logging.info(f"  {name}: {imp}")

    joblib.dump(final_clf, MODEL_PATH)
    logging.info(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
