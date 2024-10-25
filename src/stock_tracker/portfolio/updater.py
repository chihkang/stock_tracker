from ..scraper.finance_scraper import get_multiple_stock_prices
from ..utils.market_utils import get_market_from_symbol

class PortfolioUpdater:
    """處理股票價格更新相關的功能"""
    
    @staticmethod
    def update_stock_prices(stocks, symbols_to_update):
        """更新股票價格並返回更新統計"""
        prices = get_multiple_stock_prices(symbols_to_update)
        update_count = {'us': 0, 'local': 0}
        
        for stock in stocks:
            if stock['name'] in prices:
                price_info = prices[stock['name']]
                stock['price'] = price_info['price']
                stock['lastUpdated'] = price_info['timestamp']
                
                market = get_market_from_symbol(stock['name'])
                key = 'us' if market in ['NASDAQ', 'NYSE', 'NYSEARCA'] else 'local'
                update_count[key] += 1
                
        return update_count