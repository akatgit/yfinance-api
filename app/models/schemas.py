"""Pydantic response models for the yFinance Market Data API."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Quote
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Candles
# ---------------------------------------------------------------------------

class Candle(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: int


class CandlesResponse(BaseModel):
    symbol: str
    resolution: str
    count: int
    candles: List[Candle]


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

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


class StochasticPoint(BaseModel):
    date: str
    k: Optional[float] = None
    d: Optional[float] = None


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
    cci_20: List[IndicatorPoint]
    stochastic_14: List[StochasticPoint]
    obv: List[IndicatorPoint]
    vwap: List[IndicatorPoint]
    ema_20: List[IndicatorPoint]


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

class ArticleSentiment(BaseModel):
    compound: float
    positive: float
    negative: float
    neutral: float
    label: str


class NewsSentimentSummary(BaseModel):
    avg_compound: Optional[float] = None
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_pct: float
    negative_pct: float
    bullish_ratio: Optional[float] = None
    overall_label: str


class NewsItem(BaseModel):
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    published: Optional[str] = None
    url: Optional[str] = None
    sentiment: ArticleSentiment


class NewsResponse(BaseModel):
    symbol: str
    count: int
    sentiment_summary: NewsSentimentSummary
    articles: List[NewsItem]


# ---------------------------------------------------------------------------
# Buzz
# ---------------------------------------------------------------------------

class BuzzDetail(BaseModel):
    news_articles: int
    total_mentions: int
    attention_level: str
    interpretation: str


class BuzzResponse(BaseModel):
    symbol: str
    buzz: BuzzDetail


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
