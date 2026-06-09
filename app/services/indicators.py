"""Technical indicator service: computes indicators from OHLCV data using `ta`."""
from __future__ import annotations

from typing import List, Optional

import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator, EMAIndicator, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice

from app.services.market_data import get_history_df


def _round(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _series_to_points(dates, series, tail: int) -> List[dict]:
    """Convert a pandas Series into a list of {date, value} points (most recent last)."""
    points = []
    sliced_dates = dates[-tail:]
    sliced_values = series.iloc[-tail:]
    for d, v in zip(sliced_dates, sliced_values):
        points.append({"date": d.strftime("%Y-%m-%d"), "value": _round(v)})
    return points


def compute_indicators(symbol: str, tail: int = 15) -> dict:
    """Compute RSI, MACD, Bollinger Bands, ADX, ATR, SMA-50, CCI, Stochastic, OBV, VWAP, EMA-20.

    Returns the last `tail` values for each indicator so the agent can
    assess recent trends, not just the latest snapshot.
    """
    df = get_history_df(symbol, days=120)

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    dates = df.index

    # --- Original 6 indicators ---

    # RSI (14)
    rsi = RSIIndicator(close=close, window=14).rsi()

    # MACD (12, 26, 9)
    macd_ind = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    macd_line = macd_ind.macd()
    macd_signal = macd_ind.macd_signal()
    macd_hist = macd_ind.macd_diff()

    # Bollinger Bands (20, 2)
    bb = BollingerBands(close=close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband()
    bb_middle = bb.bollinger_mavg()
    bb_lower = bb.bollinger_lband()

    # ADX (14)
    adx = ADXIndicator(high=high, low=low, close=close, window=14).adx()

    # ATR (14)
    atr = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()

    # SMA (50)
    sma50 = SMAIndicator(close=close, window=50).sma_indicator()

    # --- 5 new indicators ---

    # CCI (20)
    cci = CCIIndicator(high=high, low=low, close=close, window=20).cci()

    # Stochastic Oscillator (14, smooth 3)
    stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    stoch_k = stoch.stoch()
    stoch_d = stoch.stoch_signal()

    # OBV
    obv = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()

    # VWAP
    vwap = VolumeWeightedAveragePrice(
        high=high, low=low, close=close, volume=volume
    ).volume_weighted_average_price()

    # EMA (20)
    ema20 = EMAIndicator(close=close, window=20).ema_indicator()

    # Build MACD points
    macd_points = []
    for d, m, s, h in zip(
        dates[-tail:],
        macd_line.iloc[-tail:],
        macd_signal.iloc[-tail:],
        macd_hist.iloc[-tail:],
    ):
        macd_points.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "macd": _round(m),
                "signal": _round(s),
                "histogram": _round(h),
            }
        )

    # Build Bollinger points
    bb_points = []
    for d, u, mid, low_b in zip(
        dates[-tail:],
        bb_upper.iloc[-tail:],
        bb_middle.iloc[-tail:],
        bb_lower.iloc[-tail:],
    ):
        bb_points.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "upper": _round(u),
                "middle": _round(mid),
                "lower": _round(low_b),
            }
        )

    # Build Stochastic points
    stoch_points = []
    for d, k, dd in zip(dates[-tail:], stoch_k.iloc[-tail:], stoch_d.iloc[-tail:]):
        stoch_points.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "k": _round(k),
                "d": _round(dd),
            }
        )

    return {
        "symbol": symbol.upper(),
        "as_of": dates[-1].strftime("%Y-%m-%d"),
        "current_price": _round(close.iloc[-1]),
        "rsi_14": _series_to_points(dates, rsi, tail),
        "macd": macd_points,
        "bollinger_bands_20": bb_points,
        "adx_14": _series_to_points(dates, adx, tail),
        "atr_14": _series_to_points(dates, atr, tail),
        "sma_50": _series_to_points(dates, sma50, tail),
        "cci_20": _series_to_points(dates, cci, tail),
        "stochastic_14": stoch_points,
        "obv": _series_to_points(dates, obv, tail),
        "vwap": _series_to_points(dates, vwap, tail),
        "ema_20": _series_to_points(dates, ema20, tail),
    }
