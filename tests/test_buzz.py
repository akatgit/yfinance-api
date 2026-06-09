import pytest
from tests.schemas.response_schemas import BuzzResponse

@pytest.mark.integration
class TestBuzzEndpoint:
    """Test suite for buzz endpoint - media attention scoring"""
    
    def test_buzz_valid_ticker(self, http_client, base_url, test_ticker, api_key):
        """Buzz endpoint should return valid data for known ticker"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{test_ticker}", params=params)
        assert response.status_code == 200
        
        data = response.json()
        buzz = BuzzResponse(**data)
        
        assert buzz.symbol == test_ticker.upper()
        assert buzz.buzz.news_articles >= 0
        assert buzz.buzz.total_mentions >= 0
        assert buzz.buzz.attention_level in ["low", "moderate", "high"]
        assert len(buzz.buzz.interpretation) > 0
    
    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"])
    def test_buzz_multiple_tickers(self, http_client, base_url, ticker, api_key):
        """Buzz endpoint should work for multiple valid tickers"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{ticker}", params=params)
        assert response.status_code == 200
        
        data = response.json()
        buzz = BuzzResponse(**data)
        assert buzz.symbol == ticker.upper()
    
    def test_buzz_attention_levels(self, http_client, base_url, test_ticker, api_key):
        """Buzz endpoint should categorize attention levels correctly"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{test_ticker}", params=params)
        data = response.json()
        buzz = BuzzResponse(**data)
        
        news_count = buzz.buzz.news_articles
        level = buzz.buzz.attention_level
        
        # Verify attention level logic
        if news_count >= 40:
            assert level == "high"
            assert "above-average" in buzz.buzz.interpretation.lower()
        elif news_count >= 15:
            assert level == "moderate"
            assert "moderate" in buzz.buzz.interpretation.lower()
        else:
            assert level == "low"
            assert "below-average" in buzz.buzz.interpretation.lower()
    
    def test_buzz_data_consistency(self, http_client, base_url, test_ticker, api_key):
        """Buzz news_articles should match total_mentions"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{test_ticker}", params=params)
        data = response.json()
        buzz = BuzzResponse(**data)
        
        # In current implementation, news_articles == total_mentions
        assert buzz.buzz.news_articles == buzz.buzz.total_mentions
    
    @pytest.mark.edge_case
    def test_buzz_invalid_ticker(self, http_client, base_url, invalid_ticker, api_key):
        """Buzz endpoint should handle invalid ticker gracefully"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{invalid_ticker}", params=params)
        # Should return 200 with zero news count (graceful degradation)
        assert response.status_code == 200
        
        data = response.json()
        buzz = BuzzResponse(**data)
        # Invalid ticker likely has no news
        assert buzz.buzz.news_articles >= 0
    
    @pytest.mark.performance
    def test_buzz_response_time(self, http_client, base_url, test_ticker, api_key):
        """Buzz endpoint should respond within 10 seconds (depends on news fetch)"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{test_ticker}", params=params)
        assert response.elapsed.total_seconds() < 10.0
    
    def test_buzz_interpretation_field(self, http_client, base_url, test_ticker, api_key):
        """Buzz interpretation should be meaningful and non-empty"""
        params = {"api_key": api_key} if api_key else {}
        response = http_client.get(f"{base_url}/buzz/{test_ticker}", params=params)
        data = response.json()
        buzz = BuzzResponse(**data)
        
        # Interpretation should contain meaningful text
        assert len(buzz.buzz.interpretation) > 20
        assert "attention" in buzz.buzz.interpretation.lower()
        assert "news" in buzz.buzz.interpretation.lower()
