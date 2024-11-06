# src/stock_tracker/portfolio/portfolio_manager.py
import json
from datetime import datetime
import pytz
import logging
import asyncio
from typing import Optional
from prettytable import PrettyTable, PLAIN_COLUMNS

from ..scraper.finance_scraper import get_multiple_stock_prices, update_multiple_stock_prices
from ..scraper.exchange_rate_scraper import get_exchange_rate, update_exchange_rate
from ..utils.market_utils import (
    should_update_price,
    get_market_from_symbol,
    format_market_hours,
    is_market_open
)
from ..utils.time_utils import get_current_timestamp

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, file_path='portfolio.json', gist_manager=None, force_update=False):
        """初始化投資組合管理器
        
        Args:
            file_path (str): 投資組合文件路徑
            gist_manager: Gist管理器實例
            force_update (bool): 是否強制更新所有價格，不考慮更新時間限制
        """
        self.file_path = file_path
        self.gist_manager = gist_manager
        self.force_update = force_update
        self.portfolio = None
    
    async def initialize(self):
        """非同步初始化方法"""
        self.portfolio = await self._load_portfolio()
        return self
        
    async def _load_portfolio(self):
        """優先從 Gist 讀取，如果失敗則從本地讀取"""
        if self.gist_manager:
            logger.info("嘗試從 Gist 讀取投資組合")
            portfolio_data = await self.gist_manager.read_portfolio()
            if portfolio_data:
                logger.info("從 Gist 成功載入投資組合")
                # 同時保存一份到本地
                try:
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
                    logger.info("已將 Gist 資料同步到本地")
                except Exception as e:
                    logger.warning(f"同步到本地失敗: {str(e)}")
                return portfolio_data
            else:
                logger.error("從 Gist 讀取失敗")
                raise FileNotFoundError("無法從 Gist 讀取投資組合資料")
        
        # 如果沒有 Gist 管理器或 Gist 讀取失敗，嘗試讀取本地檔案
        try:
            logger.info("嘗試從本地檔案讀取投資組合")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info("從本地檔案成功載入投資組合")
                return data
        except Exception as e:
            logger.error(f"讀取本地檔案失敗: {str(e)}")
            raise FileNotFoundError(f"無法讀取投資組合資料: {str(e)}")
            
    async def _save_portfolio(self):
        """保存到本地文件和 Gist"""
        try:
            # 更新本地檔案
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, indent=2, ensure_ascii=False)
            logger.info("已更新本地投資組合檔案")
            
            # 更新 Gist（如果有設定）
            if self.gist_manager:
                success = await self.gist_manager.update_portfolio(self.portfolio)
                if success:
                    logger.info("已更新 Gist 投資組合")
                    # 建立備份
                    await self.gist_manager.create_backup(self.portfolio)
                    logger.info("已建立 Gist 備份")
                else:
                    logger.warning("更新 Gist 失敗")
                    
        except Exception as e:
            logger.error(f"儲存投資組合失敗: {str(e)}")
            raise
    
    async def update_exchange_rate(self):
        """更新匯率"""
        try:
            # 使用非同步方法更新匯率
            new_rate = await update_exchange_rate('USD-TWD')
            self.portfolio['exchange rate'] = f"{new_rate:.2f}"
            self.portfolio['exchange_rate_updated'] = get_current_timestamp()
            print(f"已更新匯率: {new_rate:.2f} TWD/USD")
            return new_rate
        except Exception as e:
            logger.error(f"更新匯率失敗: {str(e)}")
            return float(self.portfolio['exchange rate'])
    
    def _calculate_total_value(self):
        """計算投資組合總值"""
        total_value_twd = 0
        exchange_rate = float(self.portfolio['exchange rate'])
        
        for stock in self.portfolio['stocks']:
            value_twd = stock['price'] * stock['quantity']
            if stock['currency'] == 'USD':
                value_twd *= exchange_rate
            total_value_twd += value_twd
        
        return total_value_twd
            
    async def update_prices(self):
        """更新所有價格"""
        # 確保已經初始化
        if self.portfolio is None:
            await self.initialize()
            
        await self.update_exchange_rate()
        
        symbols_to_update = []
        market_status = {}
        
        for stock in self.portfolio['stocks']:
            market = get_market_from_symbol(stock['name'])
            # 加入 force_update 參數到 should_update_price 的調用
            if should_update_price(stock['name'], stock.get('lastUpdated'), self.force_update):
                symbols_to_update.append(stock['name'])
            if market not in market_status:
                market_status[market] = is_market_open(market)
        
        self._print_market_status(market_status)
        
        if not symbols_to_update:
            if self.force_update:
                print("\n強制更新已啟用，但沒有需要更新的股票")
            else:
                print("\n股票價格更新狀態:")
                print("- 美股已收盤，使用最新收盤價")
                print("- 台股無需更新")
            
            await self._update_portfolio_calculations()
            return
            
        # 使用非同步方法更新股票價格
        prices = await update_multiple_stock_prices(symbols_to_update)
        
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
            await self._update_portfolio_calculations(
                us_stocks_count=us_stocks_count,
                local_stocks_count=local_stocks_count
            )
    
    async def _update_portfolio_calculations(self, us_stocks_count=0, local_stocks_count=0):
        """更新投資組合計算"""
        total_value_twd = self._calculate_total_value()
        old_total = self.portfolio['totalValue']
        
        if abs(total_value_twd - old_total) > 0.01:
            print("\n重新計算投資組合:")
            print(f"- 原總值: TWD {old_total:,.2f}")
            print(f"- 新總值: TWD {total_value_twd:,.2f}")
            
            # 更新總值
            self.portfolio['totalValue'] = total_value_twd
            exchange_rate = float(self.portfolio['exchange rate'])
            
            # 更新每支股票的佔比
            for stock in self.portfolio['stocks']:
                value_twd = stock['price'] * stock['quantity']
                if stock['currency'] == 'USD':
                    value_twd *= exchange_rate
                stock['percentageOfTotal'] = round((value_twd / total_value_twd) * 100, 2)
            
            # 同步到本地和 Gist
            await self._save_portfolio()
            
            # 打印更新統計
            if us_stocks_count > 0 or local_stocks_count > 0:
                print("\n更新統計:")
                if us_stocks_count > 0:
                    print(f"- 更新了 {us_stocks_count} 支美股價格（收盤價）")
                if local_stocks_count > 0:
                    print(f"- 更新了 {local_stocks_count} 支台股價格")
                print(f"- 投資組合總值變動: TWD {old_total:,.2f} → TWD {total_value_twd:,.2f}")
                
                # 顯示各股佔比變化的摘要
                print("\n投資佔比統計:")
                sorted_stocks = sorted(
                    self.portfolio['stocks'], 
                    key=lambda x: x['percentageOfTotal'], 
                    reverse=True
                )
                for stock in sorted_stocks:
                    print(f"- {stock['name']}: {stock['percentageOfTotal']}%")
    
    def _print_market_status(self, market_status):
        """打印市場狀態"""
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
    
    def print_portfolio(self):
        """打印投資組合摘要"""
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

    def get_portfolio_summary(self):
        """取得投資組合摘要統計"""
        summary = {
            'total_value': self.portfolio['totalValue'],
            'exchange_rate': self.portfolio['exchange rate'],
            'last_updated': self.portfolio.get('exchange_rate_updated'),
            'holdings': {
                'TWD': {'total': 0, 'count': 0},
                'USD': {'total': 0, 'count': 0}
            }
        }
        
        exchange_rate = float(self.portfolio['exchange rate'])
        
        for stock in self.portfolio['stocks']:
            currency = stock['currency']
            value = stock['price'] * stock['quantity']
            
            if currency == 'USD':
                summary['holdings']['USD']['total'] += value
                summary['holdings']['USD']['count'] += 1
            else:
                summary['holdings']['TWD']['total'] += value
                summary['holdings']['TWD']['count'] += 1
        
        # 轉換美股總值為台幣
        usd_in_twd = summary['holdings']['USD']['total'] * exchange_rate
        summary['holdings']['USD']['total_twd'] = usd_in_twd
        
        # 計算幣別佔比
        summary['currency_distribution'] = {
            'TWD': round((summary['holdings']['TWD']['total'] / self.portfolio['totalValue']) * 100, 2),
            'USD': round((usd_in_twd / self.portfolio['totalValue']) * 100, 2)
        }
        
        return summary

    def generate_charts(self, output_dir='plots'):
        """生成圖表"""
        from ..utils.plot_utils import create_portfolio_plots
        create_portfolio_plots(self.portfolio, output_dir)