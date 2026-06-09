from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    status: str

class RootResponse(BaseModel):
    service: str
    status: str
    endpoints: Dict[str, str]

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    currency: Optional[str] = None
    timestamp: Optional[str] = None

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

class CandleData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @field_validator('open', 'high', 'low', 'close')
    @classmethod
    def prices_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Prices must be positive')
        return v

class CandlesResponse(BaseModel):
    symbol: str
    candles: List[CandleData]

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

class BuzzDetail(BaseModel):
    news_articles: int
    total_mentions: int
    attention_level: str
    interpretation: str

class BuzzResponse(BaseModel):
    symbol: str
    buzz: BuzzDetail

class ErrorResponse(BaseModel):
    detail: str
