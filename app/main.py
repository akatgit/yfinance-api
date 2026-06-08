"""yFinance Market Data API.

A lightweight FastAPI service that provides price quotes, OHLCV candles,
technical indicators, and news headlines using yfinance.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    CandlesResponse,
    IndicatorsResponse,
    NewsResponse,
    QuoteResponse,
)
from app.services.indicators import compute_indicators
from app.services.market_data import get_candles, get_quote
from app.services.news import get_news

app = FastAPI(
    title="yFinance Market Data API",
    description=(
        "Free market data (price, candles, technical indicators, news) "
        "powered by yfinance."
    ),
    version="1.0.0",
)

# Allow Bodhi (or any client) to call this API from anywhere.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional simple API key protection. Set API_KEY env var to enable.
API_KEY = os.getenv("API_KEY", "")


def _check_key(provided: str | None) -> None:
    if API_KEY and provided != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/", tags=["meta"])
def root():
    """Health check and endpoint directory."""
    return {
        "service": "yFinance Market Data API",
        "status": "ok",
        "endpoints": {
            "quote": "/quote/{symbol}",
            "candles": "/candles/{symbol}?days=60",
            "indicators": "/indicators/{symbol}?tail=15",
            "news": "/news/{symbol}?limit=30",
        },
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "healthy"}


@app.get("/quote/{symbol}", response_model=QuoteResponse, tags=["technical"])
def quote(symbol: str, api_key: str | None = Query(default=None)):
    """Latest price quote for a symbol."""
    _check_key(api_key)
    try:
        return get_quote(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Quote error: {exc}")


@app.get("/candles/{symbol}", response_model=CandlesResponse, tags=["technical"])
def candles(
    symbol: str,
    days: int = Query(default=60, ge=5, le=365),
    api_key: str | None = Query(default=None),
):
    """Daily OHLCV candles for the last N trading days (default 60)."""
    _check_key(api_key)
    try:
        return get_candles(symbol, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Candles error: {exc}")


@app.get("/indicators/{symbol}", response_model=IndicatorsResponse, tags=["technical"])
def indicators(
    symbol: str,
    tail: int = Query(default=15, ge=1, le=60),
    api_key: str | None = Query(default=None),
):
    """All technical indicators (RSI, MACD, Bollinger, ADX, ATR, SMA-50) in one call."""
    _check_key(api_key)
    try:
        return compute_indicators(symbol, tail=tail)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Indicators error: {exc}")


@app.get("/news/{symbol}", response_model=NewsResponse, tags=["sentiment"])
def news(
    symbol: str,
    limit: int = Query(default=30, ge=1, le=50),
    api_key: str | None = Query(default=None),
):
    """Recent news headlines and summaries for a symbol."""
    _check_key(api_key)
    try:
        return get_news(symbol, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"News error: {exc}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
