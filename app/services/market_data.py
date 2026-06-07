"""Market data service: wraps yfinance for price quotes and OHLCV candles."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import yfinance as yf


def _safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    try:
        if value is None or pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def get_quote(symbol: str) -> dict:
    """Return the latest quote for a symbol using yfinance fast_info + history."""
    ticker = yf.Ticker(symbol)

    # fast_info is the quickest source of current price data
    fast = {}
    try:
        fast = dict(ticker.fast_info)
    except Exception:
        fast = {}

    # Pull the last two daily candles to compute change vs previous close
    hist = ticker.history(period="5d", interval="1d")
    if hist.empty:
        raise ValueError(f"No price data found for symbol '{symbol}'")

    last = hist.iloc[-1]
    prev_close = None
    if len(hist) >= 2:
        prev_close = _safe_float(hist.iloc[-2]["Close"])

    price = _safe_float(fast.get("last_price")) or _safe_float(last["Close"])
    prev_close = _safe_float(fast.get("previous_close")) or prev_close

    change = None
    change_pct = None
    if price is not None and prev_close is not None and prev_close != 0:
        change = round(price - prev_close, 4)
        change_pct = round((change / prev_close) * 100, 4)

    return {
        "symbol": symbol.upper(),
        "price": price,
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "day_high": _safe_float(fast.get("day_high")) or _safe_float(last["High"]),
        "day_low": _safe_float(fast.get("day_low")) or _safe_float(last["Low"]),
        "day_open": _safe_float(fast.get("open")) or _safe_float(last["Open"]),
        "volume": _safe_int(fast.get("last_volume")) or _safe_int(last["Volume"]),
        "currency": fast.get("currency"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_candles(symbol: str, days: int = 60) -> dict:
    """Return daily OHLCV candles for the given number of trading days."""
    # Request extra calendar days to cover weekends/holidays
    period_days = max(int(days * 1.6), days + 10)
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=f"{period_days}d", interval="1d")

    if hist.empty:
        raise ValueError(f"No price data found for symbol '{symbol}'")

    hist = hist.tail(days)
    candles = []
    for idx, row in hist.iterrows():
        candles.append(
            {
                "date": idx.strftime("%Y-%m-%d"),
                "open": _safe_float(row["Open"]),
                "high": _safe_float(row["High"]),
                "low": _safe_float(row["Low"]),
                "close": _safe_float(row["Close"]),
                "volume": _safe_int(row["Volume"]) or 0,
            }
        )

    return {
        "symbol": symbol.upper(),
        "resolution": "1d",
        "count": len(candles),
        "candles": candles,
    }


def get_history_df(symbol: str, days: int = 120) -> pd.DataFrame:
    """Return a raw OHLCV DataFrame for indicator computation.

    Uses a longer window so indicators like SMA-50 and ADX-14 have
    enough warm-up data to produce valid values.
    """
    period_days = max(int(days * 1.7), days + 60)
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=f"{period_days}d", interval="1d")
    if hist.empty:
        raise ValueError(f"No price data found for symbol '{symbol}'")
    return hist
