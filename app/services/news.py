"""News service: fetches company news headlines via yfinance.

Returns raw headlines and summaries. Sentiment classification is left
to the LLM agent that consumes this data — no sentiment library needed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import yfinance as yf


def _format_timestamp(ts) -> str:
    """Convert a unix timestamp or ISO string to ISO format."""
    if ts is None:
        return ""
    try:
        # yfinance sometimes returns unix seconds
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        return str(ts)
    except (TypeError, ValueError, OSError):
        return str(ts)


def get_news(symbol: str, limit: int = 30) -> dict:
    """Return recent news articles for a symbol.

    yfinance news structure has changed across versions; this handles
    both the legacy flat format and the newer nested 'content' format.
    """
    ticker = yf.Ticker(symbol)
    raw_news = []
    try:
        raw_news = ticker.news or []
    except Exception:
        raw_news = []

    articles: List[dict] = []
    for item in raw_news[:limit]:
        # Newer yfinance wraps fields inside item["content"]
        content = item.get("content", item)

        headline = (
            content.get("title")
            or content.get("headline")
            or item.get("title")
            or ""
        )
        summary = content.get("summary") or content.get("description") or ""

        # Source/provider
        provider = content.get("provider") or {}
        source = (
            provider.get("displayName")
            if isinstance(provider, dict)
            else item.get("publisher", "")
        )

        # Published date
        published = (
            content.get("pubDate")
            or content.get("displayTime")
            or _format_timestamp(item.get("providerPublishTime"))
        )

        # URL
        url = ""
        click_through = content.get("clickThroughUrl") or content.get("canonicalUrl")
        if isinstance(click_through, dict):
            url = click_through.get("url", "")
        elif isinstance(click_through, str):
            url = click_through
        else:
            url = item.get("link", "")

        if headline:
            articles.append(
                {
                    "headline": headline,
                    "summary": summary,
                    "source": source or "",
                    "published": str(published) if published else "",
                    "url": url,
                }
            )

    return {
        "symbol": symbol.upper(),
        "count": len(articles),
        "articles": articles,
    }
