"""Local smoke-test script for the yFinance Market Data API.

Run with: python test_local.py
Expects the server to be running on http://localhost:8000
(start with: uvicorn app.main:app --reload --port 8000)
"""
from __future__ import annotations

import os
import sys
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

BASE = "http://localhost:8000"
SYMBOL = "AAPL"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

# Read API key from environment so tests work whether protection is on or off
_API_KEY = os.getenv("API_KEY", "")

results: list[tuple[str, bool, str]] = []


def _url(path: str) -> str:
    """Append api_key query param if API_KEY is configured."""
    if not _API_KEY:
        return f"{BASE}{path}"
    sep = "&" if "?" in path else "?"
    return f"{BASE}{path}{sep}api_key={_API_KEY}"


def get(path: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(_url(path), timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as exc:
        return 0, {"error": str(exc)}


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))
    icon = PASS if passed else FAIL
    print(f"  {icon}  {name}" + (f" - {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n{'-' * 55}")
    print(f"  {title}")
    print(f"{'-' * 55}")


# -- Meta ---------------------------------------------------------------------
section("Meta")

status, body = get("/health")
check("GET /health -> 200", status == 200)
check("health.status == healthy", body.get("status") == "healthy")

status, body = get("/")
check("GET / -> 200", status == 200)
check("root lists buzz endpoint", "buzz" in body.get("endpoints", {}))
check("root does not list reddit", "reddit" not in body.get("endpoints", {}))

# -- Quote ---------------------------------------------------------------------
section("Quote")

status, body = get(f"/quote/{SYMBOL}")
check("GET /quote/AAPL -> 200", status == 200)
check("quote has price", body.get("price") is not None)
check("quote has change_pct", body.get("change_pct") is not None)
check("quote has volume", body.get("volume") is not None)
check("quote currency == USD", body.get("currency") == "USD")

status, _ = get("/quote/INVALIDTICKER999XYZ")
check("invalid ticker -> 404", status == 404)

# -- Candles -------------------------------------------------------------------
section("Candles")

status, body = get(f"/candles/{SYMBOL}?days=10")
check("GET /candles/AAPL?days=10 -> 200", status == 200)
check("candles count == 10", body.get("count") == 10)
check("candles resolution == 1d", body.get("resolution") == "1d")
check("candle has OHLCV keys", all(
    k in (body.get("candles") or [{}])[0]
    for k in ("open", "high", "low", "close", "volume")
))

status, body = get(f"/candles/{SYMBOL}?days=5")
check("min days=5 returns 5 candles", body.get("count") == 5)

status, _ = get(f"/candles/{SYMBOL}?days=999")
check("days=999 -> 422", status == 422)

# -- Indicators ----------------------------------------------------------------
section("Indicators")

status, body = get(f"/indicators/{SYMBOL}?tail=5")
check("GET /indicators/AAPL?tail=5 -> 200", status == 200)
check("indicators has current_price", body.get("current_price") is not None)

for field in ("rsi_14", "macd", "bollinger_bands_20", "adx_14", "atr_14", "sma_50",
              "cci_20", "stochastic_14", "obv", "vwap", "ema_20"):
    check(f"field present: {field}", field in body)

check("rsi_14 has 5 points", len(body.get("rsi_14", [])) == 5)
check("stochastic_14 has k and d keys", all(
    "k" in p and "d" in p for p in body.get("stochastic_14", [])
))
check("macd points have histogram", all(
    "histogram" in p for p in body.get("macd", [])
))

# -- News ----------------------------------------------------------------------
section("News")

status, body = get(f"/news/{SYMBOL}?limit=5")
check("GET /news/AAPL?limit=5 -> 200", status == 200)
check("news has sentiment_summary", "sentiment_summary" in body)

ss = body.get("sentiment_summary", {})
check("sentiment_summary has avg_compound", "avg_compound" in ss)
check("sentiment_summary has bullish_ratio", "bullish_ratio" in ss)
check("sentiment_summary has overall_label", "overall_label" in ss)

articles = body.get("articles", [])
if articles:
    first = articles[0]
    check("article has sentiment.compound", "compound" in first.get("sentiment", {}))
    check("article sentiment.label is valid",
          first.get("sentiment", {}).get("label") in ("positive", "negative", "neutral"))
else:
    print(f"  {WARN}  No news articles returned (yfinance may be rate-limited)")

# -- Buzz ----------------------------------------------------------------------
section("Buzz")

status, body = get(f"/buzz/{SYMBOL}")
check("GET /buzz/AAPL -> 200", status == 200)
buzz = body.get("buzz", {})
check("buzz has news_articles", "news_articles" in buzz)
check("buzz has total_mentions", "total_mentions" in buzz)
check("buzz attention_level is valid",
      buzz.get("attention_level") in ("high", "moderate", "low"))
check("buzz has interpretation", bool(buzz.get("interpretation")))
check("buzz total_mentions equals news_articles",
      buzz.get("total_mentions") == buzz.get("news_articles"))

status, _ = get("/social/reddit/AAPL")
check("/social/reddit removed -> 404 or 405", status in (404, 405))

# -- Summary -------------------------------------------------------------------
section("Summary")
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed
print(f"\n  {passed}/{total} checks passed", end="")
if failed:
    print(f"  ({failed} failed)")
    print("\n  Failed checks:")
    for name, ok, detail in results:
        if not ok:
            print(f"    X {name}" + (f"  -  {detail}" if detail else ""))
else:
    print(" OK")

sys.exit(0 if failed == 0 else 1)
