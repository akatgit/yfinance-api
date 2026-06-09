# Prompt for Claude Code: Update yfinance-api FastAPI Project

## Context

I have a FastAPI project deployed on Render at https://yfinance-api-p92p.onrender.com that provides stock market data for a multi-agent trading system. The project repo is at https://github.com/akatgit/yfinance-api/

Current project structure:
```
app/
├── main.py              # FastAPI app with routes
├── models/
│   └── schemas.py       # Pydantic response models
└── services/
    ├── market_data.py   # yfinance quote + candles
    ├── indicators.py    # ta library (RSI, MACD, Bollinger, ADX, ATR, SMA-50)
    └── news.py          # yfinance news headlines
```

Current endpoints:
- GET /quote/{symbol} — latest price
- GET /candles/{symbol}?days=60 — OHLCV data
- GET /indicators/{symbol}?tail=15 — 6 technical indicators
- GET /news/{symbol}?limit=30 — news headlines

## Task: Add 5 new features

### 1. Add VADER sentiment scoring to the /news endpoint

**Library:** `vaderSentiment`
**What to do:** Extend the existing /news/{symbol} endpoint response. For each article, compute a VADER sentiment score on the headline + summary combined text. Also add aggregated sentiment metrics to the response.

**New fields in each article object:**
```json
{
  "headline": "...",
  "summary": "...",
  "source": "...",
  "published": "...",
  "url": "...",
  "sentiment": {
    "compound": 0.6249,
    "positive": 0.45,
    "negative": 0.12,
    "neutral": 0.43,
    "label": "positive"
  }
}
```

**Label logic:** compound >= 0.05 → "positive", compound <= -0.05 → "negative", else → "neutral"

**New aggregated fields at the top level of the /news response:**
```json
{
  "symbol": "AAPL",
  "count": 25,
  "sentiment_summary": {
    "avg_compound": 0.32,
    "positive_count": 15,
    "negative_count": 5,
    "neutral_count": 5,
    "positive_pct": 60.0,
    "negative_pct": 20.0,
    "bullish_ratio": 0.75,
    "overall_label": "positive"
  },
  "articles": [...]
}
```

**bullish_ratio** = positive_count / (positive_count + negative_count). If both are zero, set to null.
**overall_label** based on avg_compound using the same thresholds.

**Add to requirements.txt:** `vaderSentiment==3.3.2`

---

### 2. New endpoint: GET /social/reddit/{symbol}

**Purpose:** Fetch recent Reddit posts mentioning a stock and compute sentiment.

**How it works:**
- Make a GET request to `https://www.reddit.com/search.json?q={symbol}+stock&sort=new&limit=25&t=week`
- Set User-Agent header to `TradingAgents/1.0 (market research bot)`
- Parse the response to extract post titles, scores, comment counts, subreddits
- Run VADER sentiment on each post title
- Aggregate the results

**Create a new service file:** `app/services/social.py`

**Response schema:**
```json
{
  "symbol": "AAPL",
  "source": "reddit",
  "posts_found": 20,
  "posts": [
    {
      "title": "AAPL looking strong after earnings",
      "subreddit": "wallstreetbets",
      "score": 245,
      "num_comments": 87,
      "created_utc": "2026-06-01T14:30:00Z",
      "sentiment": {
        "compound": 0.5423,
        "label": "positive"
      }
    }
  ],
  "sentiment_summary": {
    "avg_compound": 0.28,
    "positive_count": 12,
    "negative_count": 5,
    "neutral_count": 3,
    "positive_pct": 60.0,
    "negative_pct": 25.0,
    "bullish_ratio": 0.71,
    "overall_label": "positive"
  },
  "engagement": {
    "total_score": 1250,
    "total_comments": 430,
    "avg_score": 62.5,
    "avg_comments": 21.5,
    "top_subreddits": ["wallstreetbets", "stocks", "investing"]
  }
}
```

**Error handling:** Reddit rate-limits aggressively. If the request fails or returns 429, return a response with posts_found: 0 and a note field explaining the rate limit. Do NOT crash the endpoint.

**Add `httpx` to requirements.txt** for making the Reddit request (or use `requests`).

---

### 3. New endpoint: GET /social/stocktwits/{symbol}

**Purpose:** Fetch recent StockTwits messages and the built-in bullish/bearish sentiment.

**How it works:**
- Make a GET request to `https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json`
- No API key or auth needed
- Parse the response for messages and sentiment data

**Response schema:**
```json
{
  "symbol": "AAPL",
  "source": "stocktwits",
  "messages_found": 20,
  "messages": [
    {
      "body": "AAPL breaking out, loading up calls",
      "created_at": "2026-06-03T10:15:00Z",
      "sentiment": "bullish",
      "username": "trader123"
    }
  ],
  "sentiment_summary": {
    "bullish_count": 14,
    "bearish_count": 4,
    "neutral_count": 2,
    "bullish_pct": 70.0,
    "bearish_pct": 20.0,
    "bullish_ratio": 0.78,
    "overall_label": "bullish"
  }
}
```

**Notes on StockTwits response parsing:**
- Each message has a `entities.sentiment` field that can be `{"basic": "Bullish"}`, `{"basic": "Bearish"}`, or null (neutral).
- Extract the sentiment from there — do NOT compute it yourself. StockTwits users self-tag their sentiment.
- If the API returns an error or is unavailable, return messages_found: 0 with an error note.

**Add this to the same `app/services/social.py` file.**

---

### 4. New endpoint: GET /buzz/{symbol}

**Purpose:** Measure how much media attention a stock is getting.

**How it works:**
- Call the existing get_news function (from app/services/news.py) to get article count
- Call the reddit function (from the new social.py) to get post count
- Call the stocktwits function (from social.py) to get message count
- Combine into a buzz score

**Response schema:**
```json
{
  "symbol": "AAPL",
  "buzz": {
    "news_articles": 25,
    "reddit_posts": 18,
    "stocktwits_messages": 20,
    "total_mentions": 63,
    "attention_level": "high",
    "interpretation": "Stock is receiving above-average attention across news and social media"
  }
}
```

**attention_level logic:**
- total_mentions >= 40 → "high"
- total_mentions >= 15 → "moderate" 
- total_mentions < 15 → "low"

**Important:** This endpoint calls the other services internally. Handle errors gracefully — if Reddit or StockTwits fail, still return the buzz with available data and note which sources failed.

---

### 5. Add 5 more technical indicators to /indicators/{symbol}

**Extend `app/services/indicators.py`** to also compute and return:

**a) CCI (Commodity Channel Index, 20-period)**
```python
from ta.trend import CCIIndicator
cci = CCIIndicator(high=high, low=low, close=close, window=20).cci()
```
Return as: `"cci_20": [{date, value}, ...]`

**b) Stochastic Oscillator (14-period)**
```python
from ta.momentum import StochasticOscillator
stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
stoch_k = stoch.stoch()
stoch_d = stoch.stoch_signal()
```
Return as: `"stochastic_14": [{date, k, d}, ...]`

**c) OBV (On-Balance Volume)**
```python
from ta.volume import OnBalanceVolumeIndicator
obv = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
```
Return as: `"obv": [{date, value}, ...]`
Note: need to pass volume to the compute_indicators function. Update get_history_df and compute_indicators accordingly.

**d) VWAP (Volume Weighted Average Price)**
```python
from ta.volume import VolumeWeightedAveragePrice
vwap = VolumeWeightedAveragePrice(high=high, low=low, close=close, volume=volume).volume_weighted_average_price()
```
Return as: `"vwap": [{date, value}, ...]`

**e) EMA 20 (Exponential Moving Average, 20-period)**
```python
from ta.trend import EMAIndicator
ema20 = EMAIndicator(close=close, window=20).ema_indicator()
```
Return as: `"ema_20": [{date, value}, ...]`

**Note:** For OBV and VWAP, the volume column is needed. Make sure the compute_indicators function receives the volume data from the DataFrame. The current implementation may only pass high, low, close — update it to also use df["Volume"].

**Update the Pydantic schemas** in schemas.py to include the new indicator fields in the IndicatorsResponse model. Add new point models for Stochastic (has k and d values).

---

## General Requirements

1. **Don't break existing endpoints.** All current endpoints must continue working as before. New fields are additive.
2. **Error handling:** Every external call (Reddit, StockTwits) must be wrapped in try/except. Never crash the server because an external service is down. Return partial data with error notes.
3. **Add all new dependencies to requirements.txt:** vaderSentiment, httpx (if not already present).
4. **Update the root / endpoint** to include the new endpoints in the directory listing.
5. **Add Pydantic response models** for all new endpoints in schemas.py.
6. **Add new routes** in main.py for: /social/reddit/{symbol}, /social/stocktwits/{symbol}, /buzz/{symbol}.
7. **Tag the new routes** appropriately: social endpoints with tag "social", buzz with tag "sentiment", indicators stays "technical".
8. **Test locally** with `python test_local.py` after changes — update test_local.py to also test the new endpoints.
9. **Keep the code style consistent** with the existing codebase: type hints, docstrings, _safe_float/_round helper patterns.
10. **Timeout on external calls:** Set a 10-second timeout on Reddit and StockTwits HTTP requests. If they time out, return empty data with an error note, don't hang.
