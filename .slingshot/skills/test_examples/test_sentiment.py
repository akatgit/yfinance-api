"""Sentiment Analysis Tests - VADER Sentiment Validation

Tests for VADER sentiment analysis on news articles, including
sentiment scores, labels, and aggregated metrics.
"""
import pytest
from tests.schemas.response_schemas import NewsResponse

@pytest.mark.integration
class TestSentimentAnalysis:
    """Test suite for VADER sentiment analysis in news endpoint"""
    
    def test_news_sentiment_structure(self, http_client, base_url, test_ticker):
        """News articles should include sentiment scores"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 10})
        assert response.status_code == 200
        
        data = response.json()
        news = NewsResponse(**data)
        
        if len(news.articles) > 0:
            article = news.articles[0]
            # Validate sentiment fields
            assert article.sentiment.compound is not None
            assert article.sentiment.positive is not None
            assert article.sentiment.negative is not None
            assert article.sentiment.neutral is not None
            assert article.sentiment.label in ["positive", "negative", "neutral"]
    
    def test_sentiment_compound_range(self, http_client, base_url, test_ticker):
        """Compound sentiment score should be in range [-1, 1]"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 10})
        data = response.json()
        news = NewsResponse(**data)
        
        for article in news.articles:
            assert -1.0 <= article.sentiment.compound <= 1.0, \
                f"Compound score {article.sentiment.compound} out of range"
    
    def test_sentiment_component_scores_range(self, http_client, base_url, test_ticker):
        """Positive, negative, neutral scores should be in range [0, 1]"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 10})
        data = response.json()
        news = NewsResponse(**data)
        
        for article in news.articles:
            assert 0.0 <= article.sentiment.positive <= 1.0
            assert 0.0 <= article.sentiment.negative <= 1.0
            assert 0.0 <= article.sentiment.neutral <= 1.0
    
    def test_sentiment_label_logic(self, http_client, base_url, test_ticker):
        """Sentiment label should match compound score thresholds"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 10})
        data = response.json()
        news = NewsResponse(**data)
        
        for article in news.articles:
            compound = article.sentiment.compound
            label = article.sentiment.label
            
            if compound >= 0.05:
                assert label == "positive", f"Expected 'positive' for {compound}, got {label}"
            elif compound <= -0.05:
                assert label == "negative", f"Expected 'negative' for {compound}, got {label}"
            else:
                assert label == "neutral", f"Expected 'neutral' for {compound}, got {label}"
    
    def test_sentiment_summary_structure(self, http_client, base_url, test_ticker):
        """News response should include sentiment summary"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 20})
        data = response.json()
        news = NewsResponse(**data)
        
        summary = news.sentiment_summary
        assert summary is not None
        assert hasattr(summary, "avg_compound")
        assert hasattr(summary, "positive_count")
        assert hasattr(summary, "negative_count")
        assert hasattr(summary, "neutral_count")
        assert hasattr(summary, "positive_pct")
        assert hasattr(summary, "negative_pct")
        assert hasattr(summary, "bullish_ratio")
        assert hasattr(summary, "overall_label")
    
    def test_sentiment_summary_counts(self, http_client, base_url, test_ticker):
        """Sentiment summary counts should sum to total articles"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 20})
        data = response.json()
        news = NewsResponse(**data)
        
        if news.count > 0:
            summary = news.sentiment_summary
            total_counted = summary.positive_count + summary.negative_count + summary.neutral_count
            assert total_counted == news.count, \
                f"Count mismatch: {total_counted} != {news.count}"
    
    def test_sentiment_summary_percentages(self, http_client, base_url, test_ticker):
        """Sentiment percentages should be valid"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 20})
        data = response.json()
        news = NewsResponse(**data)
        
        if news.count > 0:
            summary = news.sentiment_summary
            # Percentages should be in range [0, 100]
            assert 0.0 <= summary.positive_pct <= 100.0
            assert 0.0 <= summary.negative_pct <= 100.0
            # Sum should be <= 100 (neutral makes up the rest)
            assert summary.positive_pct + summary.negative_pct <= 100.0
    
    def test_sentiment_bullish_ratio(self, http_client, base_url, test_ticker):
        """Bullish ratio should be in range [0, 1] when defined"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 20})
        data = response.json()
        news = NewsResponse(**data)
        
        summary = news.sentiment_summary
        if summary.bullish_ratio is not None:
            assert 0.0 <= summary.bullish_ratio <= 1.0, \
                f"Bullish ratio {summary.bullish_ratio} out of range"
    
    def test_sentiment_overall_label(self, http_client, base_url, test_ticker):
        """Overall sentiment label should match average compound"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": 20})
        data = response.json()
        news = NewsResponse(**data)
        
        if news.count > 0:
            summary = news.sentiment_summary
            avg_compound = summary.avg_compound
            overall_label = summary.overall_label
            
            if avg_compound >= 0.05:
                assert overall_label == "positive"
            elif avg_compound <= -0.05:
                assert overall_label == "negative"
            else:
                assert overall_label == "neutral"
    
    @pytest.mark.edge_case
    def test_sentiment_empty_news(self, http_client, base_url, invalid_ticker):
        """Sentiment summary should handle empty news gracefully"""
        response = http_client.get(f"{base_url}/news/{invalid_ticker}", params={"limit": 10})
        data = response.json()
        news = NewsResponse(**data)
        
        if news.count == 0:
            summary = news.sentiment_summary
            assert summary.avg_compound is None or summary.avg_compound == 0
            assert summary.positive_count == 0
            assert summary.negative_count == 0
            assert summary.neutral_count == 0
            assert summary.overall_label == "neutral"
    
    @pytest.mark.parametrize("limit", [5, 10, 20, 30])
    def test_sentiment_various_sample_sizes(self, http_client, base_url, test_ticker, limit):
        """Sentiment analysis should work for various sample sizes"""
        response = http_client.get(f"{base_url}/news/{test_ticker}", params={"limit": limit})
        data = response.json()
        news = NewsResponse(**data)
        
        # Should have valid sentiment summary regardless of sample size
        assert news.sentiment_summary is not None
        assert news.sentiment_summary.overall_label in ["positive", "negative", "neutral"]
