class PortfolioCalculator:
    """投資組合計算器，處理所有數值計算相關功能"""
    
    @staticmethod
    def calculate_total_value(stocks, exchange_rate):
        """計算投資組合總值"""
        return sum(
            stock['price'] * stock['quantity'] * (exchange_rate if stock['currency'] == 'USD' else 1)
            for stock in stocks
        )

    @staticmethod
    def update_percentages(stocks, total_value_twd, exchange_rate):
        """更新投資組合的佔比"""
        for stock in stocks:
            value_twd = stock['price'] * stock['quantity']
            if stock['currency'] == 'USD':
                value_twd *= exchange_rate
            stock['percentageOfTotal'] = round((value_twd / total_value_twd) * 100, 2)