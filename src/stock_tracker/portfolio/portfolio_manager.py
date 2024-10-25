import json
from ..scraper.exchange_rate_scraper import get_exchange_rate
from ..utils.market_utils import should_update_price, get_market_from_symbol, is_market_open
from ..utils.time_utils import get_current_timestamp
from .calculator import PortfolioCalculator
from .formatter import PortfolioFormatter
from .updater import PortfolioUpdater

class PortfolioManager:
    def __init__(self, file_path='portfolio.json'):
        self.file_path = file_path
        self.portfolio = self._load_portfolio()
        self.calculator = PortfolioCalculator()
        self.formatter = PortfolioFormatter()
        self.updater = PortfolioUpdater()

    def _load_portfolio(self):
        """載入投資組合資料"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_portfolio(self):
        """儲存投資組合資料"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.portfolio, f, indent=2, ensure_ascii=False)

    def update_exchange_rate(self):
        """更新匯率"""
        try:
            new_rate = get_exchange_rate('USD-TWD')
            self.portfolio['exchange rate'] = f"{new_rate:.2f}"
            self.portfolio['exchange_rate_updated'] = get_current_timestamp()
            print(f"已更新匯率: {new_rate:.2f} TWD/USD")
            return new_rate
        except Exception as e:
            print(f"更新匯率失敗: {str(e)}")
            return float(self.portfolio['exchange rate'])

    def update_prices(self):
        """更新所有股票價格"""
        self.update_exchange_rate()
        exchange_rate = float(self.portfolio['exchange rate'])
        needs_recalculation = False
        
        # 收集更新資訊
        symbols_to_update = []
        market_status = {}
        
        for stock in self.portfolio['stocks']:
            market = get_market_from_symbol(stock['name'])
            if should_update_price(stock['name'], stock.get('lastUpdated')):
                symbols_to_update.append(stock['name'])
            if market not in market_status:
                market_status[market] = is_market_open(market)
                # 如果任何市場開盤中，就需要重新計算佔比
                if market_status[market]:
                    needs_recalculation = True
        
        self.formatter.print_market_status(market_status)
        
        # 即使沒有股票需要更新價格，也要檢查是否需要重新計算佔比
        if not symbols_to_update and needs_recalculation:
            self._recalculate_portfolio()
            return
        elif not symbols_to_update:
            print("\n股票價格更新狀態:")
            print("- 所有市場均已收盤，使用最新收盤價")
            return
            
        self._handle_price_updates(symbols_to_update)

    def _recalculate_portfolio(self):
        """重新計算投資組合總值和佔比"""
        exchange_rate = float(self.portfolio['exchange rate'])
        total_value_twd = self.calculator.calculate_total_value(
            self.portfolio['stocks'], 
            exchange_rate
        )
        
        if abs(total_value_twd - self.portfolio['totalValue']) > 0.01:
            print("\n重新計算投資組合:")
            print(f"- 原總值: TWD {self.portfolio['totalValue']:,.2f}")
            print(f"- 新總值: TWD {total_value_twd:,.2f}")
            
            self.portfolio['totalValue'] = total_value_twd
            self.calculator.update_percentages(
                self.portfolio['stocks'],
                total_value_twd,
                exchange_rate
            )
            self._save_portfolio()
            print("- 已更新投資組合佔比")

    def _handle_no_updates(self):
        """處理無需更新的情況"""
        print("\n股票價格更新狀態:")
        print("- 美股已收盤，使用最新收盤價")
        print("- 台股無需更新")
        
        exchange_rate = float(self.portfolio['exchange rate'])
        total_value_twd = self.calculator.calculate_total_value(
            self.portfolio['stocks'], 
            exchange_rate
        )
        
        if abs(total_value_twd - self.portfolio['totalValue']) > 0.01:
            print("\n重新計算投資組合:")
            print(f"- 原總值: TWD {self.portfolio['totalValue']:,.2f}")
            print(f"- 新總值: TWD {total_value_twd:,.2f}")
            
            self.portfolio['totalValue'] = total_value_twd
            self.calculator.update_percentages(
                self.portfolio['stocks'],
                total_value_twd,
                exchange_rate
            )
            self._save_portfolio()
            print("- 已更新投資組合佔比")

    def _handle_price_updates(self, symbols_to_update):
        """處理需要更新價格的情況"""
        update_count = self.updater.update_stock_prices(
            self.portfolio['stocks'],
            symbols_to_update
        )
        
        if sum(update_count.values()) > 0:
            exchange_rate = float(self.portfolio['exchange rate'])
            old_total = self.portfolio['totalValue']
            total_value_twd = self.calculator.calculate_total_value(
                self.portfolio['stocks'],
                exchange_rate
            )
            
            self.portfolio['totalValue'] = total_value_twd
            self.calculator.update_percentages(
                self.portfolio['stocks'],
                total_value_twd,
                exchange_rate
            )
            
            self._save_portfolio()
            self.formatter.print_update_summary(update_count, old_total, total_value_twd)

    def print_portfolio(self):
        """顯示投資組合資訊"""
        table = self.formatter.create_table()
        exchange_rate = float(self.portfolio['exchange rate'])
        
        # 添加資料行
        for stock in self.portfolio['stocks']:
            value_twd = stock['price'] * stock['quantity']
            if stock['currency'] == 'USD':
                value_twd *= exchange_rate
            
            table.add_row([
                stock['name'],
                f"{stock['currency']} {stock['price']:.2f}",
                f"{stock['quantity']:,.2f}",
                f"TWD {value_twd:,.2f}",
                f"{stock['percentageOfTotal']:.2f}%",
                stock['lastUpdated']
            ])
        
        # 輸出內容
        table_width = len(table.get_string().split('\n')[0])
        separator = "=" * table_width
        divider = "-" * table_width
        
        print("\n投資組合摘要:")
        print(separator)
        print(f"總價值: TWD {self.portfolio['totalValue']:,.2f}")
        print(f"匯率: {self.portfolio['exchange rate']} TWD/USD")
        print(divider)
        print(table.get_string())
        print(separator)