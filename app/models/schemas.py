"""Pydantic response models for the yFinance Market Data API."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class QuoteResponse(BaseModel):
    symbol: str
    price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    day_open: Optional[float] = None
    volume: Optional[int] = None
    currency: Optional[str] = None
    timestamp: Optional[str] = None


class Candle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class CandlesResponse(BaseModel):
    symbol: str
    resolution: str
    count: int
    candles: List[Candle]


class IndicatorPoint(BaseModel):
    date: str
    value: Optional[float] = None


class MACDPoint(BaseModel):
    date: str
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None


class BollingerPoint(BaseModel):
    date: str
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None


class IndicatorsResponse(BaseModel):
    symbol: str
    as_of: str
    current_price: Optional[float] = None
    rsi_14: List[IndicatorPoint]
    macd: List[MACDPoint]
    bollinger_bands_20: List[BollingerPoint]
    adx_14: List[IndicatorPoint]
    atr_14: List[IndicatorPoint]
    sma_50: List[IndicatorPoint]


class NewsItem(BaseModel):
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    published: Optional[str] = None
    url: Optional[str] = None


class NewsResponse(BaseModel):
    symbol: str
    count: int
    articles: List[NewsItem]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
