"""Buzz Endpoint Tests - Media Attention Scoring

Tests for the /buzz/{symbol} endpoint that provides media attention scoring
based on news article volume.
"""
import pytest
from tests.schemas.response_schemas import BuzzResponse

@pytest.mark.integration
class TestBuzzEndpoint:
    """Test suite for buzz endpoint - media attention scoring"""
    
    def test_buzz_valid_ticker(self, http_client, base_url, test_ticker):
        """Buzz endpoint should return valid data for known ticker"""
        response = http_client.get(f"{base_url}/buzz/{test_ticker}")
        assert response.status_code == 200
        
        data = response.json()
        buzz = BuzzResponse(**data)
        
        assert buzz.symbol == test_ticker.upper()
        assert buzz.buzz.news_articles >= 0
        assert buzz.buzz.total_mentions >= 0
        assert buzz.buzz.attention_level in ["low", "moderate", "high"]
    
    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"])
    def test_buzz_multiple_tickers(self, http_client, base_url, ticker):
        """Buzz endpoint should work for multiple valid tickers"""
        response = http_client.get(f"{base_url}/buzz/{ticker}")
        assert response.status_code == 200
        
        data = response.json()
        buzz = BuzzResponse(**data)
        assert buzz.symbol == ticker.upper()
    
    def test_buzz_attention_level_logic(self, http_client, base_url, test_ticker):
        """Buzz attention level should follow correct thresholds"""
        response = http_client.get(f"{base_url}/buzz/{test_ticker}")
        data = response.json()
        buzz = BuzzResponse(**data)
        
        news_count = buzz.buzz.news_articles
        level = buzz.buzz.attention_level
        
        # Validate attention level thresholds
        if news_count >= 40:
            assert level == "high", f"Expected 'high' for {news_count} articles, got {level}"
        elif news_count >= 15:
            assert level == "moderate", f"Expected 'moderate' for {news_count} articles, got {level}"
        else:
            assert level == "low", f"Expected 'low' for {news_count} articles, got {level}"
    
    def test_buzz_interpretation_field(self, http_client, base_url, test_ticker):
        """Buzz response should include interpretation text"""
        response = http_client.get(f"{base_url}/buzz/{test_ticker}")
        data = response.json()
        buzz = BuzzResponse(**data)
        
        assert buzz.buzz.interpretation is not None
        assert len(buzz.buzz.interpretation) > 0
        assert "attention" in buzz.buzz.interpretation.lower()
    
    def test_buzz_total_mentions_equals_articles(self, http_client, base_url, test_ticker):
        """Total mentions should equal news articles count"""
        response = http_client.get(f"{base_url}/buzz/{test_ticker}")
        data = response.json()
        buzz = BuzzResponse(**data)
        
        # Current implementation: total_mentions = news_articles
        assert buzz.buzz.total_mentions == buzz.buzz.news_articles
    
    @pytest.mark.edge_case
    def test_buzz_invalid_ticker(self, http_client, base_url, invalid_ticker):
        """Buzz endpoint should handle invalid ticker gracefully"""
        response = http_client.get(f"{base_url}/buzz/{invalid_ticker}")
        # Should return 200 with zero counts (graceful degradation)
        assert response.status_code == 200
        
        data = response.json()
        buzz = BuzzResponse(**data)
        # Invalid ticker likely has no news
        assert buzz.buzz.news_articles >= 0
    
    @pytest.mark.edge_case
    def test_buzz_with_api_key(self, http_client, base_url, test_ticker, api_key):
        """Buzz endpoint should respect API key authentication"""
        if api_key:
            response = http_client.get(
                f"{base_url}/buzz/{test_ticker}",
                params={"api_key": api_key}
            )
            assert response.status_code == 200
    
    @pytest.mark.performance
    def test_buzz_response_time(self, http_client, base_url, test_ticker):
        """Buzz endpoint should respond within 10 seconds"""
        response = http_client.get(f"{base_url}/buzz/{test_ticker}")
        assert response.elapsed.total_seconds() < 10.0
    
    def test_buzz_response_structure(self, http_client, base_url, test_ticker):
        """Buzz response should have correct nested structure"""
        response = http_client.get(f"{base_url}/buzz/{test_ticker}")
        data = response.json()
        
        # Validate structure
        assert "symbol" in data
        assert "buzz" in data
        assert "news_articles" in data["buzz"]
        assert "total_mentions" in data["buzz"]
        assert "attention_level" in data["buzz"]
        assert "interpretation" in data["buzz"]
