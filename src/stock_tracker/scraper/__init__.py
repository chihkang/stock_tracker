"""
股票資訊爬蟲模組
"""

from .finance_scraper import get_stock_price, get_multiple_stock_prices

__all__ = ['get_stock_price', 'get_multiple_stock_prices']