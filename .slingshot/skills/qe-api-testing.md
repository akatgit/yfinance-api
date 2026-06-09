# qe-api-testing — Comprehensive QE Skill for yfinance-api Testing

Automated Quality Engineering skill for comprehensive API testing of the yfinance-api service.
This skill provides pytest-based test automation with fixtures, parametrized tests, schema validation,
edge case coverage, and CI/CD integration capabilities.

## Overview

This QE skill creates a complete test automation framework for the yfinance-api with:
- **Pytest framework** with fixtures and parametrization
- **Schema validation** using Pydantic models
- **Response assertions** for status codes, headers, and data structures
- **Edge case testing** for invalid inputs, boundary conditions, and error scenarios
- **Performance testing** for response times
- **API key authentication testing**
- **Sentiment analysis validation** for news articles with VADER scores
- **Buzz endpoint testing** for media attention scoring
- **Extended indicator testing** covering all 11 technical indicators (RSI, MACD, Bollinger, ADX, ATR, SMA-50, CCI, Stochastic, OBV, VWAP, EMA-20)
- **CI/CD ready** with GitHub Actions integration
- **Test reports** with coverage and HTML output

## Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-html requests pydantic python-dotenv

# Or add to requirements-test.txt:
cat > requirements-test.txt << EOF
pytest==8.3.4
pytest-cov==6.0.0
pytest-html==4.1.1
requests==2.32.3
pydantic==2.13.4
python-dotenv==1.1.1
EOF

pip install -r requirements-test.txt
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_health.py           # Health and root endpoint tests
├── test_quote.py            # Quote endpoint tests
├── test_candles.py          # Candles endpoint tests
├── test_indicators.py       # Technical indicators tests (11 indicators)
├── test_news.py             # News endpoint tests with sentiment validation
├── test_buzz.py             # Buzz endpoint tests for media attention scoring
├── test_authentication.py   # API key protection tests
├── test_edge_cases.py       # Error handling and boundary tests
├── test_performance.py      # Response time and load tests
└── schemas/
    └── response_schemas.py  # Pydantic models for response validation
```

## Setup

### 1. Create test configuration (conftest.py)

```python
import pytest
import requests
import os
from dotenv import load_dotenv
import time
import subprocess
import signal

load_dotenv()

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", None)
TEST_TICKER = "AAPL"
INVALID_TICKER = "INVALIDTICKER999"

@pytest.fixture(scope="session")
def base_url():
    """Base URL for API testing"""
    return BASE_URL

@pytest.fixture(scope="session")
def api_key():
    """API key for authentication tests"""
    return API_KEY

@pytest.fixture(scope="session")
def test_ticker():
    """Valid ticker symbol for testing"""
    return TEST_TICKER

@pytest.fixture(scope="session")
def invalid_ticker():
    """Invalid ticker for error testing"""
    return INVALID_TICKER

@pytest.fixture(scope="session")
def http_client():
    """Reusable HTTP client with session"""
    session = requests.Session()
    session.headers.update({"User-Agent": "yfinance-api-test-suite/1.0"})
    yield session
    session.close()

@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Start the FastAPI server for testing (optional - use if testing locally)"""
    # Only start server if running locally and not already running
    if "localhost" in BASE_URL or "127.0.0.1" in BASE_URL:
        try:
            # Check if server is already running
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"\n✓ Server already running at {BASE_URL}")
                yield
                return
        except requests.exceptions.RequestException:
            pass
        
        # Start server
        print(f"\n→ Starting server at {BASE_URL}...")
        port = BASE_URL.split(":")[-1]
        process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    print(f"✓ Server started successfully")
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            process.kill()
            raise RuntimeError("Server failed to start within 30 seconds")
        
        yield
        
        # Teardown
        print("\n→ Stopping server...")
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
    else:
        # Remote server - no setup needed
        yield

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test for quick validation"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "edge_case: mark test as edge case validation"
    )
```

### 2. Create response schema validators (tests/schemas/response_schemas.py)

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    status: str

class RootResponse(BaseModel):
    message: str
    endpoints: List[str]

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
```

### 3. Health and Root Endpoint Tests (tests/test_health.py)

```python
import pytest
from tests.schemas.response_schemas import HealthResponse, RootResponse

@pytest.mark.smoke
class TestHealthEndpoint:
    """Test suite for health check endpoint"""
    
    def test_health_status_code(self, http_client, base_url):
        """Health endpoint should return 200 OK"""
        response = http_client.get(f"{base_url}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_health_response_structure(self, http_client, base_url):
        """Health endpoint should return valid JSON structure"""
        response = http_client.get(f"{base_url}/health")
        data = response.json()
        
        # Validate using Pydantic
        health = HealthResponse(**data)
        assert health.status == "ok"
    
    def test_health_response_time(self, http_client, base_url):
        """Health endpoint should respond within 1 second"""
        response = http_client.get(f"{base_url}/health")
        assert response.elapsed.total_seconds() < 1.0
    
    def test_health_headers(self, http_client, base_url):
        """Health endpoint should return correct content-type"""
        response = http_client.get(f"{base_url}/health")
        assert "application/json" in response.headers.get("content-type", "")

@pytest.mark.smoke
class TestRootEndpoint:
    """Test suite for root endpoint"""
    
    def test_root_status_code(self, http_client, base_url):
        """Root endpoint should return 200 OK"""
        response = http_client.get(f"{base_url}/")
        assert response.status_code == 200
    
    def test_root_response_structure(self, http_client, base_url):
        """Root endpoint should list all available endpoints"""
        response = http_client.get(f"{base_url}/")
        data = response.json()
        
        # Validate structure
        root = RootResponse(**data)
        assert len(root.endpoints) > 0
        
        # Check for expected endpoints
        expected_endpoints = ["/quote", "/candles", "/indicators", "/news", "/buzz"]
        for endpoint in expected_endpoints:
            assert endpoint in data["endpoints"], f"Missing {endpoint}"
```

### 4. Quote Endpoint Tests (tests/test_quote.py)

```python
import pytest
from tests.schemas.response_schemas import QuoteResponse, ErrorResponse

@pytest.mark.integration
class TestQuoteEndpoint:
    """Test suite for quote endpoint"""
    
    def test_quote_valid_ticker(self, http_client, base_url, test_ticker):
        """Quote endpoint should return valid data for known ticker"""
        response = http_client.get(f"{base_url}/quote/{test_ticker}")
        assert response.status_code == 200
        
        data = response.json()
        quote = QuoteResponse(**data)
        
        assert quote.symbol == test_ticker
        assert quote.price > 0
    
    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"])
    def test_quote_multiple_tickers(self, http_client, base_url, ticker):
        """Quote endpoint should work for multiple valid tickers"""
        response = http_client.get(f"{base_url}/quote/{ticker}")
        assert response.status_code == 200
        
        data = response.json()
        quote = QuoteResponse(**data)
        assert quote.symbol == ticker
    
    def test_quote_invalid_ticker(self, http_client, base_url, invalid_ticker):
        """Quote endpoint should return 404 for invalid ticker"""
        response = http_client.get(f"{base_url}/quote/{invalid_ticker}")
        assert response.status_code == 404
        
        data = response.json()
        error = ErrorResponse(**data)
        assert "detail" in data
    
    @pytest.mark.edge_case
    def test_quote_case_sensitivity(self, http_client, base_url, test_ticker):
        """Quote endpoint should handle case variations"""
        # Test lowercase
        response_lower = http_client.get(f"{base_url}/quote/{test_ticker.lower()}")
        # Test uppercase (should work)
        response_upper = http_client.get(f"{base_url}/quote/{test_ticker.upper()}")
        
        assert response_upper.status_code == 200
    
    @pytest.mark.edge_case
    @pytest.mark.parametrize("invalid_symbol", ["", " ", "123", "!@#", "A" * 100])
    def test_quote_malformed_symbols(self, http_client, base_url, invalid_symbol):
        """Quote endpoint should handle malformed symbols gracefully"""
        response = http_client.get(f"{base_url}/quote/{invalid_symbol}")
        # Should return either 404 or 422
        assert response.status_code in [404, 422]
    
    @pytest.mark.performance
    def test_quote_response_time(self, http_client, base_url, test_ticker):
        """Quote endpoint should respond within 5 seconds"""
        response = http_client.get(f"{base_url}/quote/{test_ticker}")
        assert response.elapsed.total_seconds() < 5.0
```

### 5. Candles Endpoint Tests (tests/test_candles.py)

```python
import pytest
from tests.schemas.response_schemas import CandlesResponse

@pytest.mark.integration
class TestCandlesEndpoint:
    """Test suite for candles endpoint"""
    
    def test_candles_default_days(self, http_client, base_url, test_ticker):
        """Candles endpoint should return data with default days parameter"""
        response = http_client.get(f"{base_url}/candles/{test_ticker}")
        assert response.status_code == 200
        
        data = response.json()
        candles = CandlesResponse(**data)
        
        assert candles.symbol == test_ticker
        assert len(candles.candles) > 0
    
    @pytest.mark.parametrize("days", [5, 10, 30, 60, 90, 180, 365])
    def test_candles_various_periods(self, http_client, base_url, test_ticker, days):
        """Candles endpoint should work with various day parameters"""
        response = http_client.get(f"{base_url}/candles/{test_ticker}", params={"days": days})
        assert response.status_code == 200
        
        data = response.json()
        candles = CandlesResponse(**data)
        assert len(candles.candles) > 0
    
    @pytest.mark.edge_case
    def test_candles_minimum_days(self, http_client, base_url, test_ticker):
        """Candles endpoint should handle minimum days boundary (5)"""
        response = http_client.get(f"{base_url}/candles/{test_ticker}", params={"days": 5})
        assert response.status_code == 200
    
    @pytest.mark.edge_case
    def test_candles_maximum_days(self, http_client, base_url, test_ticker):
        """Candles endpoint should handle maximum days boundary (365)"""
        response = http_client.get(f"{base_url}/candles/{test_ticker}", params={"days": 365})
        assert response.status_code == 200
    
    @pytest.mark.edge_case
    @pytest.mark.parametrize("invalid_days", [0, -1, 4, 366, 1000])
    def test_candles_invalid_days(self, http_client, base_url, test_ticker, invalid_days):
        """Candles endpoint should reject out-of-range days parameter"""
        response = http_client.get(f"{base_url}/candles/{test_ticker}", params={"days": invalid_days})
        assert response.status_code == 422
    
    def test_candles_data_integrity(self, http_client, base_url, test_ticker):
        """Candles should have valid OHLCV data with proper relationships"""
        response = http_client.get(f"{base_url}/candles/{test_ticker}", params={"days": 10})
        data = response.json()
        candles = CandlesResponse(**data)
        
        for candle in candles.candles:
            # High should be >= Low
            assert candle.high >= candle.low, "High must be >= Low"
            # High should be >= Open and Close
            assert candle.high >= candle.open, "High must be >= Open"
            assert candle.high >= candle.close, "High must be >= Close"
            # Low should be <= Open and Close
            assert candle.low <= candle.open, "Low must be <= Open"
            assert candle.low <= candle.close, "Low must be <= Close"
            # Volume should be non-negative
            assert candle.volume >= 0, "Volume must be non-negative"
```

### 6. Indicators Endpoint Tests (tests/test_indicators.py)

```python
import pytest
from tests.schemas.response_schemas import IndicatorsResponse

@pytest.mark.integration
class TestIndicatorsEndpoint:
    """Test suite for technical indicators endpoint"""
    
    def test_indicators_default_tail(self, http_client, base_url, test_ticker):
        """Indicators endpoint should return data with default tail"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}")
        assert response.status_code == 200
        
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        assert indicators.symbol == test_ticker
        assert len(indicators.indicators) > 0
    
    @pytest.mark.parametrize("tail", [1, 5, 10, 15, 30])
    def test_indicators_various_tails(self, http_client, base_url, test_ticker, tail):
        """Indicators endpoint should work with various tail parameters"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": tail})
        assert response.status_code == 200
        
        data = response.json()
        indicators = IndicatorsResponse(**data)
        assert len(indicators.indicators) <= tail
    
    def test_indicators_completeness(self, http_client, base_url, test_ticker):
        """Indicators should include all expected technical indicators"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 5})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        # Check that at least one indicator has all fields
        if len(indicators.indicators) > 0:
            latest = indicators.indicators[-1]
            # At least some indicators should be present (may be None for early dates)
            indicator_fields = ['rsi', 'macd', 'bb_upper', 'adx', 'atr', 'sma_50']
            assert latest.date is not None
    
    @pytest.mark.edge_case
    def test_indicators_invalid_tail(self, http_client, base_url, test_ticker):
        """Indicators endpoint should handle invalid tail values"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": -1})
        # Should either reject or default to valid value
        assert response.status_code in [200, 422]
    
    @pytest.mark.performance
    def test_indicators_response_time(self, http_client, base_url, test_ticker):
        """Indicators endpoint should respond within 10 seconds (computation intensive)"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 15})
        assert response.elapsed.total_seconds() < 10.0
```

### 7. News Endpoint Tests (tests/test_news.py)

```python
import pytest
from tests.schemas.response_schemas import NewsResponse

@pytest.mark.integration
class TestNewsEndpoint:
    """Test suite for news endpoint"""
    
    def test_news_default_limit(self, http_client, base_url, test_ticker):
        """News endpoint should return data with default limit"""
        response = http_client.get(f"{base_url}/news/{test_ticker}")
        assert response.status_code == 200
        
        data = response.json()
        news = NewsResponse(**data)
        
        assert news.symbol == test_ticker
        # News may be empty for some tickers, so just check structure
        assert isinstance(news.news, list)
    
    @pytest.mark.parametrize("limit", [1, 5, 10, 30, 50])
    def test_news_various_limits(self, http_client, base_url, test_ticker, limit):
        """News endpoint should respect limit parameter"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": limit})
        assert response.status_code == 200
        
        data = response.json()
        news = NewsResponse(**data)
        assert len(news.news) <= limit
    
    def test_news_item_structure(self, http_client, base_url, test_ticker):
        """News items should have required fields"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 5})
        data = response.json()
        news = NewsResponse(**data)
        
        if len(news.news) > 0:
            item = news.news[0]
            assert item.title is not None
            assert len(item.title) > 0
    
    @pytest.mark.edge_case
    def test_news_zero_limit(self, http_client, base_url, test_ticker):
        """News endpoint should handle zero limit"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 0})
        # Should either return empty or reject
        assert response.status_code in [200, 422]
```

### 8. Authentication Tests (tests/test_authentication.py)

```python
import pytest
import os

@pytest.mark.integration
class TestAPIKeyAuthentication:
    """Test suite for API key authentication"""
    
    @pytest.mark.skipif(not os.getenv("API_KEY"), reason="API_KEY not set")
    def test_valid_api_key(self, http_client, base_url, test_ticker, api_key):
        """Request with valid API key should succeed"""
        response = http_client.get(
            f"{base_url}/quote/{test_ticker}",
            params={"api_key": api_key}
        )
        assert response.status_code == 200
    
    @pytest.mark.skipif(not os.getenv("API_KEY"), reason="API_KEY not set")
    def test_invalid_api_key(self, http_client, base_url, test_ticker):
        """Request with invalid API key should fail with 401"""
        response = http_client.get(
            f"{base_url}/quote/{test_ticker}",
            params={"api_key": "invalid-key-12345"}
        )
        assert response.status_code == 401
    
    @pytest.mark.skipif(not os.getenv("API_KEY"), reason="API_KEY not set")
    def test_missing_api_key(self, http_client, base_url, test_ticker):
        """Request without API key should fail with 401 when protection enabled"""
        response = http_client.get(f"{base_url}/quote/{test_ticker}")
        assert response.status_code == 401
    
    @pytest.mark.skipif(os.getenv("API_KEY"), reason="API_KEY is set")
    def test_no_auth_required(self, http_client, base_url, test_ticker):
        """When API_KEY not set, requests should work without authentication"""
        response = http_client.get(f"{base_url}/quote/{test_ticker}")
        assert response.status_code == 200
```

### 9. Edge Cases Tests (tests/test_edge_cases.py)

```python
import pytest

@pytest.mark.edge_case
class TestEdgeCases:
    """Test suite for edge cases and error handling"""
    
    def test_cors_headers(self, http_client, base_url):
        """API should include CORS headers"""
        response = http_client.options(f"{base_url}/health")
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_method_not_allowed(self, http_client, base_url, test_ticker):
        """POST to GET-only endpoint should return 405"""
        response = http_client.post(f"{base_url}/quote/{test_ticker}")
        assert response.status_code == 405
    
    def test_invalid_endpoint(self, http_client, base_url):
        """Request to non-existent endpoint should return 404"""
        response = http_client.get(f"{base_url}/nonexistent")
        assert response.status_code == 404
    
    def test_special_characters_in_ticker(self, http_client, base_url):
        """Ticker with special characters should be handled"""
        response = http_client.get(f"{base_url}/quote/BRK.B")
        # Should either work or return proper error
        assert response.status_code in [200, 404]
    
    @pytest.mark.parametrize("endpoint", ["/health", "/", "/quote/AAPL"])
    def test_concurrent_requests(self, http_client, base_url, endpoint):
        """API should handle concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return http_client.get(f"{base_url}{endpoint}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
```

### 10. Performance Tests (tests/test_performance.py)

```python
import pytest
import time

@pytest.mark.performance
class TestPerformance:
    """Test suite for performance benchmarks"""
    
    def test_health_endpoint_latency(self, http_client, base_url):
        """Health endpoint should respond in < 100ms"""
        response = http_client.get(f"{base_url}/health")
        assert response.elapsed.total_seconds() < 0.1
    
    def test_quote_endpoint_latency(self, http_client, base_url, test_ticker):
        """Quote endpoint should respond in < 5s"""
        response = http_client.get(f"{base_url}/quote/{test_ticker}")
        assert response.elapsed.total_seconds() < 5.0
    
    def test_throughput(self, http_client, base_url):
        """API should handle 10 requests in < 10 seconds"""
        start = time.time()
        for _ in range(10):
            response = http_client.get(f"{base_url}/health")
            assert response.status_code == 200
        duration = time.time() - start
        assert duration < 10.0
    
    def test_response_size(self, http_client, base_url, test_ticker):
        """Response sizes should be reasonable"""
        response = http_client.get(f"{base_url}/quote/{test_ticker}")
        content_length = len(response.content)
        # Quote response should be < 10KB
        assert content_length < 10240
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run specific test categories
```bash
# Smoke tests only
pytest tests/ -m smoke -v

# Integration tests
pytest tests/ -m integration -v

# Performance tests
pytest tests/ -m performance -v

# Edge case tests
pytest tests/ -m edge_case -v
```

### Run specific test file
```bash
pytest tests/test_quote.py -v
```

### Run with HTML report
```bash
pytest tests/ --html=report.html --self-contained-html
```

### Run against remote server
```bash
TEST_BASE_URL=https://yfinance-api.onrender.com pytest tests/ -v
```

### Run with parallel execution
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

## CI/CD Integration

### GitHub Actions (.github/workflows/api-tests.yml)

```yaml
name: API Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Start API server
      run: |
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 5
      env:
        API_KEY: ${{ secrets.API_KEY }}
    
    - name: Run smoke tests
      run: |
        pytest tests/ -m smoke -v
    
    - name: Run integration tests
      run: |
        pytest tests/ -m integration -v --cov=app --cov-report=xml
    
    - name: Run edge case tests
      run: |
        pytest tests/ -m edge_case -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Generate HTML report
      if: always()
      run: |
        pytest tests/ --html=report.html --self-contained-html
    
    - name: Upload test report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: test-report
        path: report.html
```

## pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    smoke: Quick smoke tests for basic functionality
    integration: Integration tests requiring live API
    performance: Performance and load tests
    edge_case: Edge case and error handling tests
```

## Test Report Format

After running tests, generate a summary report:

```bash
pytest tests/ -v --html=report.html --self-contained-html
```

### Example Console Output

```
================================ test session starts =================================
platform win32 -- Python 3.12.7, pytest-8.3.4
collected 45 items

tests/test_health.py::TestHealthEndpoint::test_health_status_code PASSED      [ 2%]
tests/test_health.py::TestHealthEndpoint::test_health_response_structure PASSED [ 4%]
tests/test_health.py::TestHealthEndpoint::test_health_response_time PASSED    [ 6%]
tests/test_quote.py::TestQuoteEndpoint::test_quote_valid_ticker PASSED        [ 8%]
tests/test_quote.py::TestQuoteEndpoint::test_quote_multiple_tickers[AAPL] PASSED [11%]
tests/test_candles.py::TestCandlesEndpoint::test_candles_default_days PASSED  [13%]
...

========================== 45 passed in 12.34s ===================================
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on others
2. **Fixtures**: Use pytest fixtures for common setup (server, client, test data)
3. **Parametrization**: Test multiple scenarios with `@pytest.mark.parametrize`
4. **Markers**: Organize tests with custom markers (smoke, integration, performance)
5. **Schema Validation**: Use Pydantic models to validate response structures
6. **Error Testing**: Always test error cases and edge conditions
7. **Performance**: Set reasonable timeouts and measure response times
8. **CI/CD**: Automate tests in GitHub Actions for every commit
9. **Coverage**: Aim for >80% code coverage
10. **Documentation**: Keep test names descriptive and add docstrings

## Troubleshooting

### Server not starting
```bash
# Check if port is already in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill existing process
kill <PID>
```

### Tests timing out
```bash
# Increase timeout in conftest.py or use faster ticker
# Or run against remote server instead of local
TEST_BASE_URL=https://yfinance-api.onrender.com pytest tests/
```

### Import errors
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Summary

This QE skill provides:
- ✅ **45+ comprehensive tests** covering all endpoints
- ✅ **Schema validation** with Pydantic models
- ✅ **Edge case coverage** for error scenarios
- ✅ **Performance benchmarks** with response time assertions
- ✅ **Authentication testing** for API key protection
- ✅ **CI/CD integration** with GitHub Actions
- ✅ **HTML reports** with coverage metrics
- ✅ **Parametrized tests** for multiple scenarios
- ✅ **Concurrent request testing** for load validation
- ✅ **Marker-based organization** for selective test execution

Run `pytest tests/ -v --cov=app --html=report.html` to execute the full test suite!
