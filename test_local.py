"""Quick local test script. Run AFTER installing requirements.

Usage:
    python test_local.py

This calls each service function directly (no server needed) and prints
sample output so you can verify yfinance + ta are working before deploying.
"""
from app.services.market_data import get_quote, get_candles
from app.services.indicators import compute_indicators
from app.services.news import get_news

SYMBOL = "AAPL"


def main():
    print(f"Testing with symbol: {SYMBOL}\n")

    print("=" * 50)
    print("QUOTE")
    print("=" * 50)
    quote = get_quote(SYMBOL)
    for k, v in quote.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 50)
    print("CANDLES (last 5 of 60)")
    print("=" * 50)
    candles = get_candles(SYMBOL, days=60)
    print(f"  Total candles: {candles['count']}")
    for c in candles["candles"][-5:]:
        print(f"  {c['date']}: O={c['open']} H={c['high']} "
              f"L={c['low']} C={c['close']} V={c['volume']}")

    print("\n" + "=" * 50)
    print("INDICATORS (latest values)")
    print("=" * 50)
    ind = compute_indicators(SYMBOL, tail=15)
    print(f"  Current price: {ind['current_price']}")
    print(f"  RSI-14:  {ind['rsi_14'][-1]}")
    print(f"  MACD:    {ind['macd'][-1]}")
    print(f"  BBands:  {ind['bollinger_bands_20'][-1]}")
    print(f"  ADX-14:  {ind['adx_14'][-1]}")
    print(f"  ATR-14:  {ind['atr_14'][-1]}")
    print(f"  SMA-50:  {ind['sma_50'][-1]}")

    print("\n" + "=" * 50)
    print("NEWS (first 3)")
    print("=" * 50)
    news = get_news(SYMBOL, limit=30)
    print(f"  Total articles: {news['count']}")
    for a in news["articles"][:3]:
        print(f"  - {a['headline']} ({a['source']})")

    print("\n[OK] All services working.")


if __name__ == "__main__":
    main()
