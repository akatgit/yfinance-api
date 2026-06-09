# verifier-api — yfinance-api Server Verifier

Launches the FastAPI server, exercises every endpoint against a real
ticker, captures raw responses, then tears down. Use this skill any
time you need to verify the yfinance-api is working correctly.

## Setup

```bash
# Activate the venv and start the server in the background
cd c:/amit/ai-handson/yfinance-api
source venv/Scripts/activate
uvicorn app.main:app --host 0.0.0.0 --port 8765 &
SERVER_PID=$!
sleep 5   # give uvicorn time to bind
```

## Drive

Run each curl against `http://localhost:8765`. Capture full response bodies.

### 1. Health check
```bash
curl -s http://localhost:8765/health
```

### 2. Root — endpoint directory
```bash
curl -s http://localhost:8765/
```

### 3. Quote — latest price (use AAPL as a known-good ticker)
```bash
curl -s http://localhost:8765/quote/AAPL
```

### 4. Candles — OHLCV history (default 60 days)
```bash
curl -s http://localhost:8765/candles/AAPL?days=10
```

### 5. Indicators — all technical indicators
```bash
curl -s "http://localhost:8765/indicators/AAPL?tail=5"
```

### 6. News — headlines with sentiment
```bash
curl -s "http://localhost:8765/news/AAPL?limit=3"
```

### 7. Buzz — media attention score
```bash
curl -s http://localhost:8765/buzz/AAPL
```

## Probes (edge cases)

### 8. Invalid ticker — expect 404
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/quote/INVALIDTICKER999
```

### 9. API key protection — set a key, then test with and without it
```bash
# Start a second instance with a key set (skip if testing is already done above)
# Instead, test the _check_key guard by calling the running server
# with ?api_key= when API_KEY env var is NOT set (should always pass through)
curl -s "http://localhost:8765/quote/AAPL?api_key=anything"
```

### 10. Candles boundary — minimum days
```bash
curl -s "http://localhost:8765/candles/AAPL?days=5"
```

### 11. Buzz with low-volume ticker (expect low attention)
```bash
curl -s http://localhost:8765/buzz/ZZZZ
```

## Teardown

```bash
kill $SERVER_PID 2>/dev/null
```

## Report format

Follow the standard verify skill report:

```
## Verification: yfinance-api endpoints

**Verdict:** PASS | FAIL | BLOCKED

**Claim:** All five data endpoints (quote, candles, indicators, news, buzz)
return valid JSON with expected fields for a real ticker symbol.

**Method:** Cold-start uvicorn on port 8765, curl each route, kill server.

### Steps
1. ✅/❌ health → ...
2. ✅/❌ root → ...
3. ✅/❌ quote/AAPL → ...
4. ✅/❌ candles/AAPL?days=10 → ...
5. ✅/❌ indicators/AAPL?tail=5 → ...
6. ✅/❌ news/AAPL?limit=3 → ...
7. ✅/❌ buzz/AAPL → ...
🔍 invalid ticker → ...
🔍 api_key passthrough → ...
🔍 candles min days → ...
🔍 buzz low-volume ticker → ...

### Findings
<anything that made you pause>
```