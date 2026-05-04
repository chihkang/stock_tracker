import pytest
from unittest.mock import patch, MagicMock
from stock_tracker.scraper.finance_scraper import get_stock_price
from stock_tracker.exceptions import ScraperError

@pytest.fixture
def mock_response():
    """模擬網路請求回應"""
    response = MagicMock()
    response.text = '{"regularMarketPrice":{"raw":100.50}}'
    return response

def test_get_stock_price_success(mock_response):
    """測試成功取得股價"""
    with patch('requests.get') as mock_get:
        mock_get.return_value = mock_response
        
        price_info = get_stock_price("TSLA:NASDAQ")
        
        assert price_info["price"] == 100.50
        assert price_info["currency"] == "USD"
        assert price_info["timestamp"] is not None

def test_get_stock_price_network_error():
    """測試網路錯誤情況"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(ScraperError):
            get_stock_price("TSLA:NASDAQ")
