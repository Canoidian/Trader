import time
import logging

_regime_cache = None
_regime_cache_time = 0.0
_CACHE_TTL = 600  # 10 minutes


def calculate_adx(highs, lows, closes, period=14):
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
    if adx < 20:
        return 'SIDEWAYS', 65.0
    if price > sma200:
        return 'BULL', 60.0
    return 'BEAR', 78.0


def get_market_regime(api):
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
