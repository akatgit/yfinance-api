"""Technical indicator service: computes indicators from OHLCV data using `ta`."""
from __future__ import annotations

from typing import List, Optional

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands

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
    """Compute RSI, MACD, Bollinger Bands, ADX, ATR, and SMA-50.

    Returns the last `tail` values for each indicator so the agent can
    assess recent trends, not just the latest snapshot.
    """
    df = get_history_df(symbol, days=120)

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    dates = df.index

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
    }
