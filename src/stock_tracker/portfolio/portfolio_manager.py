import json
from datetime import datetime
import pytz
from prettytable import PrettyTable, PLAIN_COLUMNS
from stock_tracker.scraper.finance_scraper import get_multiple_stock_prices
from stock_tracker.scraper.exchange_rate_scraper import get_exchange_rate
from stock_tracker.utils.market_utils import (
    should_update_price,
    get_market_from_symbol,
    format_market_hours,
    is_market_open
)
from stock_tracker.utils.time_utils import get_current_timestamp

class PortfolioManager:
    def __init__(self, file_path='portfolio.json'):
        self.file_path = file_path
        self.portfolio = self._load_portfolio()
        
    def _load_portfolio(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _save_portfolio(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.portfolio, f, indent=2, ensure_ascii=False)
    
    def update_exchange_rate(self):
        try:
            new_rate = get_exchange_rate('USD-TWD')
            self.portfolio['exchange rate'] = f"{new_rate:.2f}"
            self.portfolio['exchange_rate_updated'] = get_current_timestamp()
            print(f"已更新匯率: {new_rate:.2f} TWD/USD")
            return new_rate
        except Exception as e:
            print(f"更新匯率失敗: {str(e)}")
            return float(self.portfolio['exchange rate'])
    
    def _calculate_total_value(self):
        total_value_twd = 0
        exchange_rate = float(self.portfolio['exchange rate'])
        
        for stock in self.portfolio['stocks']:
            value_twd = stock['price'] * stock['quantity']
            if stock['currency'] == 'USD':
                value_twd *= exchange_rate
            total_value_twd += value_twd
        
        return total_value_twd
            
    def update_prices(self):
        self.update_exchange_rate()
        
        symbols_to_update = []
        market_status = {}
        
        for stock in self.portfolio['stocks']:
            market = get_market_from_symbol(stock['name'])
            if should_update_price(stock['name'], stock.get('lastUpdated')):
                symbols_to_update.append(stock['name'])
            if market not in market_status:
                market_status[market] = is_market_open(market)
        
        print("\n市場狀態:")
        for market, is_open in market_status.items():
            trading_hours = format_market_hours(market)
            if market in ['NASDAQ', 'NYSE', 'NYSEARCA']:
                if is_open:
                    print(f"{market}: {trading_hours} - 交易中")
                else:
                    print(f"{market}: {trading_hours} - 收盤中 (使用最新收盤價)")
            else:
                if is_open:
                    print(f"{market}: {trading_hours} - 交易中")
                else:
                    print(f"{market}: {trading_hours} - 收盤中")
        
        if not symbols_to_update:
            print("\n股票價格更新狀態:")
            print("- 美股已收盤，使用最新收盤價")
            print("- 台股無需更新")
            
            total_value_twd = self._calculate_total_value()
            if abs(total_value_twd - self.portfolio['totalValue']) > 0.01:
                print("\n重新計算投資組合:")
                print(f"- 原總值: TWD {self.portfolio['totalValue']:,.2f}")
                print(f"- 新總值: TWD {total_value_twd:,.2f}")
                
                self.portfolio['totalValue'] = total_value_twd
                exchange_rate = float(self.portfolio['exchange rate'])
                for stock in self.portfolio['stocks']:
                    value_twd = stock['price'] * stock['quantity']
                    if stock['currency'] == 'USD':
                        value_twd *= exchange_rate
                    stock['percentageOfTotal'] = round((value_twd / total_value_twd) * 100, 2)
                
                self._save_portfolio()
                print("- 已更新投資組合佔比")
            return
            
        prices = get_multiple_stock_prices(symbols_to_update)
        
        update_count = 0
        us_stocks_count = 0
        local_stocks_count = 0
        
        for stock in self.portfolio['stocks']:
            if stock['name'] in prices:
                price_info = prices[stock['name']]
                stock['price'] = price_info['price']
                stock['lastUpdated'] = price_info['timestamp']
                update_count += 1
                
                market = get_market_from_symbol(stock['name'])
                if market in ['NASDAQ', 'NYSE', 'NYSEARCA']:
                    us_stocks_count += 1
                else:
                    local_stocks_count += 1
        
        if update_count > 0 or local_stocks_count > 0:
            total_value_twd = self._calculate_total_value()
            old_total = self.portfolio['totalValue']
            self.portfolio['totalValue'] = total_value_twd
            
            exchange_rate = float(self.portfolio['exchange rate'])
            for stock in self.portfolio['stocks']:
                value_twd = stock['price'] * stock['quantity']
                if stock['currency'] == 'USD':
                    value_twd *= exchange_rate
                stock['percentageOfTotal'] = round((value_twd / total_value_twd) * 100, 2)
            
            self._save_portfolio()
            
            print("\n更新統計:")
            if us_stocks_count > 0:
                print(f"- 更新了 {us_stocks_count} 支美股價格（收盤價）")
            if local_stocks_count > 0:
                print(f"- 更新了 {local_stocks_count} 支台股價格")
            if abs(total_value_twd - old_total) > 0.01:
                print(f"- 投資組合總值變動: TWD {old_total:,.2f} → TWD {total_value_twd:,.2f}")
    
    def print_portfolio(self):
        table = PrettyTable()
        table.set_style(PLAIN_COLUMNS)
        
        table.field_names = ["股票代號", "價格", "數量", "總值 (TWD)", "比例", "更新時間"]
        
        for field in table.field_names:
            table.align[field] = "l"
        
        min_widths = {
            "股票代號": 15,
            "價格": 15,
            "數量": 15,
            "總值 (TWD)": 20,
            "比例": 10,
            "更新時間": 35
        }
        for field, width in min_widths.items():
            table._min_width[field] = width

        table.border = False
        
        exchange_rate = float(self.portfolio['exchange rate'])
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
        
        table_width = len(table.get_string().split('\n')[0])
        separator = "=" * table_width
        divider = "-" * table_width
        
        # Get current time in Taipei timezone
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz)
        formatted_time = current_time.strftime('%Y/%m/%d %H:%M')
        
        print("\n投資組合摘要:")
        print(separator)
        print(f"日期時間: {formatted_time}")
        print(f"總價值: TWD {self.portfolio['totalValue']:,.2f}")
        print(f"匯率: {self.portfolio['exchange rate']} TWD/USD")
        print(divider)
        print(table.get_string())
        print(separator)

    def generate_charts(self, output_dir='plots'):
        from stock_tracker.utils.plot_utils import create_portfolio_plots
        create_portfolio_plots(self.portfolio, output_dir)