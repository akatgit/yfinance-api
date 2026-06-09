"""News service: fetches company news headlines via yfinance and scores sentiment.

Sentiment is computed with VADER on the combined headline + summary text.
Aggregated metrics are also returned so agents can assess overall mood.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def _sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def _score(text: str) -> dict:
    scores = _analyzer.polarity_scores(text)
    compound = round(scores["compound"], 4)
    return {
        "compound": compound,
        "positive": round(scores["pos"], 4),
        "negative": round(scores["neg"], 4),
        "neutral": round(scores["neu"], 4),
        "label": _sentiment_label(compound),
    }


def _format_timestamp(ts) -> str:
    if ts is None:
        return ""
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        return str(ts)
    except (TypeError, ValueError, OSError):
        return str(ts)


def _sentiment_summary(articles: List[dict]) -> dict:
    if not articles:
        return {
            "avg_compound": None,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "bullish_ratio": None,
            "overall_label": "neutral",
        }

    compounds = [a["sentiment"]["compound"] for a in articles]
    avg_compound = round(sum(compounds) / len(compounds), 4)
    pos = sum(1 for a in articles if a["sentiment"]["label"] == "positive")
    neg = sum(1 for a in articles if a["sentiment"]["label"] == "negative")
    neu = len(articles) - pos - neg
    n = len(articles)
    bullish_ratio: Optional[float] = round(pos / (pos + neg), 4) if (pos + neg) > 0 else None

    return {
        "avg_compound": avg_compound,
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "positive_pct": round(pos / n * 100, 2),
        "negative_pct": round(neg / n * 100, 2),
        "bullish_ratio": bullish_ratio,
        "overall_label": _sentiment_label(avg_compound),
    }


def get_news(symbol: str, limit: int = 30) -> dict:
    """Return recent news articles with VADER sentiment scores for a symbol."""
    ticker = yf.Ticker(symbol)
    raw_news = []
    try:
        raw_news = ticker.news or []
    except Exception:
        raw_news = []

    articles: List[dict] = []
    for item in raw_news[:limit]:
        content = item.get("content", item)

        headline = (
            content.get("title")
            or content.get("headline")
            or item.get("title")
            or ""
        )
        summary = content.get("summary") or content.get("description") or ""

        provider = content.get("provider") or {}
        source = (
            provider.get("displayName")
            if isinstance(provider, dict)
            else item.get("publisher", "")
        )

        published = (
            content.get("pubDate")
            or content.get("displayTime")
            or _format_timestamp(item.get("providerPublishTime"))
        )

        url = ""
        click_through = content.get("clickThroughUrl") or content.get("canonicalUrl")
        if isinstance(click_through, dict):
            url = click_through.get("url", "")
        elif isinstance(click_through, str):
            url = click_through
        else:
            url = item.get("link", "")

        if headline:
            text = f"{headline}. {summary}".strip()
            articles.append(
                {
                    "headline": headline,
                    "summary": summary,
                    "source": source or "",
                    "published": str(published) if published else "",
                    "url": url,
                    "sentiment": _score(text),
                }
            )

    return {
        "symbol": symbol.upper(),
        "count": len(articles),
        "sentiment_summary": _sentiment_summary(articles),
        "articles": articles,
    }
