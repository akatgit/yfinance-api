"""Extended Indicators Tests - All 11 Technical Indicators

Comprehensive tests for all technical indicators:
- RSI (14)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- ADX (14)
- ATR (14)
- SMA-50
- CCI (20)
- Stochastic Oscillator (14, 3)
- OBV
- VWAP
- EMA-20
"""
import pytest
from tests.schemas.response_schemas import IndicatorsResponse

@pytest.mark.integration
class TestExtendedIndicators:
    """Test suite for all 11 technical indicators"""
    
    def test_all_indicators_present(self, http_client, base_url, test_ticker):
        """Response should include all 11 technical indicators"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        assert response.status_code == 200
        
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        # Validate all 11 indicators are present
        assert hasattr(indicators, "rsi_14")
        assert hasattr(indicators, "macd")
        assert hasattr(indicators, "bollinger_bands_20")
        assert hasattr(indicators, "adx_14")
        assert hasattr(indicators, "atr_14")
        assert hasattr(indicators, "sma_50")
        assert hasattr(indicators, "cci_20")
        assert hasattr(indicators, "stochastic_14")
        assert hasattr(indicators, "obv")
        assert hasattr(indicators, "vwap")
        assert hasattr(indicators, "ema_20")
    
    def test_rsi_range(self, http_client, base_url, test_ticker):
        """RSI values should be in range [0, 100]"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for point in indicators.rsi_14:
            if point.value is not None:
                assert 0 <= point.value <= 100, f"RSI {point.value} out of range"
    
    def test_macd_structure(self, http_client, base_url, test_ticker):
        """MACD should have macd, signal, and histogram values"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for macd_point in indicators.macd:
            assert hasattr(macd_point, "macd")
            assert hasattr(macd_point, "signal")
            assert hasattr(macd_point, "histogram")
            assert hasattr(macd_point, "date")
    
    def test_bollinger_bands_structure(self, http_client, base_url, test_ticker):
        """Bollinger Bands should have upper, middle, lower values"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for bb_point in indicators.bollinger_bands_20:
            assert hasattr(bb_point, "upper")
            assert hasattr(bb_point, "middle")
            assert hasattr(bb_point, "lower")
            assert hasattr(bb_point, "date")
    
    def test_bollinger_bands_relationship(self, http_client, base_url, test_ticker):
        """Bollinger Bands: upper >= middle >= lower"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for bb_point in indicators.bollinger_bands_20:
            if all([bb_point.upper, bb_point.middle, bb_point.lower]):
                assert bb_point.upper >= bb_point.middle, "Upper band should be >= middle"
                assert bb_point.middle >= bb_point.lower, "Middle should be >= lower band"
    
    def test_adx_range(self, http_client, base_url, test_ticker):
        """ADX values should be in range [0, 100]"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for point in indicators.adx_14:
            if point.value is not None:
                assert 0 <= point.value <= 100, f"ADX {point.value} out of range"
    
    def test_atr_positive(self, http_client, base_url, test_ticker):
        """ATR values should be positive"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for point in indicators.atr_14:
            if point.value is not None:
                assert point.value >= 0, f"ATR {point.value} should be non-negative"
    
    def test_sma_50_positive(self, http_client, base_url, test_ticker):
        """SMA-50 values should be positive for stock prices"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for point in indicators.sma_50:
            if point.value is not None:
                assert point.value > 0, f"SMA-50 {point.value} should be positive"
    
    def test_cci_typical_range(self, http_client, base_url, test_ticker):
        """CCI typically ranges from -100 to +100 (can exceed)"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        # CCI can exceed ±100, but should be reasonable
        for point in indicators.cci_20:
            if point.value is not None:
                assert -500 <= point.value <= 500, f"CCI {point.value} seems unreasonable"
    
    def test_stochastic_structure(self, http_client, base_url, test_ticker):
        """Stochastic should have %K and %D values"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for stoch_point in indicators.stochastic_14:
            assert hasattr(stoch_point, "k")
            assert hasattr(stoch_point, "d")
            assert hasattr(stoch_point, "date")
    
    def test_stochastic_range(self, http_client, base_url, test_ticker):
        """Stochastic %K and %D should be in range [0, 100]"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for stoch_point in indicators.stochastic_14:
            if stoch_point.k is not None:
                assert 0 <= stoch_point.k <= 100, f"Stochastic %K {stoch_point.k} out of range"
            if stoch_point.d is not None:
                assert 0 <= stoch_point.d <= 100, f"Stochastic %D {stoch_point.d} out of range"
    
    def test_obv_trend(self, http_client, base_url, test_ticker):
        """OBV should be a cumulative volume indicator"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        # OBV can be positive or negative, no strict range
        assert len(indicators.obv) > 0
        for point in indicators.obv:
            assert point.value is not None or point.value == 0
    
    def test_vwap_positive(self, http_client, base_url, test_ticker):
        """VWAP should be positive for stock prices"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for point in indicators.vwap:
            if point.value is not None:
                assert point.value > 0, f"VWAP {point.value} should be positive"
    
    def test_ema_20_positive(self, http_client, base_url, test_ticker):
        """EMA-20 should be positive for stock prices"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        for point in indicators.ema_20:
            if point.value is not None:
                assert point.value > 0, f"EMA-20 {point.value} should be positive"
    
    def test_current_price_present(self, http_client, base_url, test_ticker):
        """Response should include current price"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        assert indicators.current_price is not None
        assert indicators.current_price > 0
    
    def test_as_of_date_present(self, http_client, base_url, test_ticker):
        """Response should include as_of date"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 10})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        assert indicators.as_of is not None
        assert len(indicators.as_of) > 0
        # Should be in YYYY-MM-DD format
        assert "-" in indicators.as_of
    
    @pytest.mark.parametrize("tail", [1, 5, 10, 15, 30, 60])
    def test_tail_parameter_respected(self, http_client, base_url, test_ticker, tail):
        """All indicators should respect tail parameter"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": tail})
        data = response.json()
        indicators = IndicatorsResponse(**data)
        
        # Each indicator should have at most 'tail' data points
        assert len(indicators.rsi_14) <= tail
        assert len(indicators.macd) <= tail
        assert len(indicators.bollinger_bands_20) <= tail
        assert len(indicators.adx_14) <= tail
        assert len(indicators.atr_14) <= tail
        assert len(indicators.sma_50) <= tail
        assert len(indicators.cci_20) <= tail
        assert len(indicators.stochastic_14) <= tail
        assert len(indicators.obv) <= tail
        assert len(indicators.vwap) <= tail
        assert len(indicators.ema_20) <= tail
    
    @pytest.mark.performance
    def test_all_indicators_performance(self, http_client, base_url, test_ticker):
        """Computing all 11 indicators should complete within 15 seconds"""
        response = http_client.get(f"{base_url}/indicators/{test_ticker}", params={"tail": 30})
        assert response.elapsed.total_seconds() < 15.0
