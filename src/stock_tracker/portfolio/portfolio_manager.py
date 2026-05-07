# src/stock_tracker/portfolio/portfolio_manager.py
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import pytz
import logging
from prettytable import PrettyTable, PLAIN_COLUMNS

from ..scraper.exchange_rate_scraper import ExchangeRateService
from ..providers.market_data import ExchangeRateFailure, MarketDataService, PriceFailure
from ..utils.market_utils import (
    should_update_price,
    get_market_from_symbol,
    format_market_hours,
    is_market_open
)
from ..utils.time_utils import get_current_timestamp

logger = logging.getLogger(__name__)
HISTORY_FILENAME = "portfolio-history.json"


@dataclass
class UpdateResult:
    status: str
    updated_symbols: list
    failed_symbols: list

class PortfolioManager:
    def __init__(
        self,
        file_path='portfolio.json',
        gist_manager=None,
        force_update=False,
        price_service=None,
        exchange_rate_service=None,
    ):
        """初始化投資組合管理器
        
        Args:
            file_path (str): 投資組合文件路徑
            gist_manager: Gist管理器實例
            force_update (bool): 是否強制更新所有價格，不考慮更新時間限制
        """
        self.file_path = file_path
        self.gist_manager = gist_manager
        self.force_update = force_update
        self.price_service = price_service or MarketDataService()
        self.exchange_rate_service = exchange_rate_service or ExchangeRateService()
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
            
    async def _save_portfolio(self, update_history=False):
        """保存到本地文件和 Gist"""
        try:
            history_data = None
            if update_history:
                history_data = await self._build_history_data()

            # 更新本地檔案
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, indent=2, ensure_ascii=False)
            logger.info("已更新本地投資組合檔案")
            if history_data is not None:
                self._save_local_history(history_data)
            
            # 更新 Gist（如果有設定）
            if self.gist_manager:
                success = await self.gist_manager.update_portfolio(self.portfolio, history_data=history_data)
                if success:
                    logger.info("已更新 Gist 投資組合")
                    # 建立備份
                    await self.gist_manager.create_backup(self.portfolio)
                    logger.info("已建立 Gist 備份")
                else:
                    logger.error("更新 Gist 失敗")
                    raise RuntimeError("更新 Gist 失敗")
                    
        except Exception as e:
            logger.error(f"儲存投資組合失敗: {str(e)}")
            raise

    async def _build_history_data(self):
        if self.gist_manager and hasattr(self.gist_manager, "read_history"):
            history_data = await self.gist_manager.read_history()
            if isinstance(history_data, dict) and not history_data.get("values"):
                local_history = self._load_local_history()
                if local_history.get("values"):
                    history_data = local_history
        else:
            history_data = self._load_local_history()

        if not isinstance(history_data, dict):
            history_data = {"values": []}

        entry = self._current_history_entry()
        values = [
            value for value in history_data.get("values", [])
            if isinstance(value, dict) and value.get("date") != entry["date"]
        ]
        values.append(entry)
        values.sort(key=lambda value: value.get("date", ""))

        updated_history = deepcopy(history_data)
        updated_history["updatedAt"] = entry["sourceUpdatedAt"]
        updated_history["values"] = values
        return updated_history

    def _current_history_entry(self):
        retrieved_at = self.portfolio.get("updateStatus", {}).get("retrieved_at") or get_current_timestamp()
        return {
            "date": self._taipei_date_key(retrieved_at),
            "totalValueTwd": self.portfolio["totalValue"],
            "sourceUpdatedAt": retrieved_at,
        }

    def _taipei_date_key(self, timestamp):
        try:
            normalized = timestamp.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = pytz.timezone("Asia/Taipei").localize(parsed)
            return parsed.astimezone(pytz.timezone("Asia/Taipei")).date().isoformat()
        except Exception:
            return str(timestamp)[:10]

    def _history_file_path(self):
        return Path(self.file_path).with_name(HISTORY_FILENAME)

    def _load_local_history(self):
        history_path = self._history_file_path()
        if not history_path.exists():
            return {"values": []}
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_local_history(self, history_data):
        with open(self._history_file_path(), "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        logger.info("已更新本地投資組合歷史檔案")
    
    async def update_exchange_rate(self):
        """更新匯率"""
        try:
            new_rate = await self.exchange_rate_service.get_rate('USD-TWD')
            if isinstance(new_rate, ExchangeRateFailure):
                raise new_rate
            self.portfolio['exchange rate'] = f"{new_rate:.2f}"
            self.portfolio['exchange_rate_updated'] = get_current_timestamp()
            print(f"已更新匯率: {new_rate:.2f} TWD/USD")
            return {
                "status": "success",
                "usedPreviousRate": False,
                "rate": self.portfolio["exchange rate"],
                "updatedAt": self.portfolio["exchange_rate_updated"],
            }
        except Exception as e:
            old_rate = self.portfolio['exchange rate']
            old_updated = self.portfolio.get('exchange_rate_updated')
            message = f"匯率更新失敗，使用舊匯率: {old_rate}"
            if old_updated:
                message = f"{message}, exchange_rate_updated: {old_updated}"
            logger.error("%s。原始錯誤: %s", message, str(e))
            return {
                "status": "failed",
                "usedPreviousRate": True,
                "reason": getattr(e, "reason", "rate_unavailable"),
                "message": message,
                "rate": old_rate,
                "updatedAt": old_updated,
            }
    
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
        if self.portfolio is None:
            await self.initialize()

        original_portfolio = deepcopy(self.portfolio)
        exchange_status = await self.update_exchange_rate()

        symbols_to_update = []
        market_status = {}

        for stock in self.portfolio['stocks']:
            market = get_market_from_symbol(stock['name'])
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
            self._update_portfolio_calculations()
            return UpdateResult(status="success", updated_symbols=[], failed_symbols=[])

        batch = await self.price_service.get_prices(symbols_to_update)
        failures = self._ordered_failures(symbols_to_update, batch)

        update_count = 0
        us_stocks_count = 0
        local_stocks_count = 0
        updated_symbols = []

        for stock in self.portfolio['stocks']:
            if stock['name'] in batch.prices:
                price_info = batch.prices[stock['name']]
                stock['price'] = price_info.price
                stock['lastUpdated'] = price_info.retrieved_at
                update_count += 1
                updated_symbols.append(stock['name'])

                market = get_market_from_symbol(stock['name'])
                if market in ['NASDAQ', 'NYSE', 'NYSEARCA']:
                    us_stocks_count += 1
                else:
                    local_stocks_count += 1

        if update_count == 0:
            self.portfolio = original_portfolio
            self.portfolio["updateStatus"] = self._build_update_status(
                status="failed",
                updated_symbols=[],
                failures=failures,
                exchange_status=exchange_status,
                message="沒有任何股票成功更新，保留既有投資組合資料",
            )
            await self._save_portfolio()
            return UpdateResult(
                status="failed",
                updated_symbols=[],
                failed_symbols=[failure.to_status_dict() for failure in failures],
            )

        status = "success" if update_count == len(symbols_to_update) else "partial_success"
        self._update_portfolio_calculations()
        self.portfolio["updateStatus"] = self._build_update_status(
            status=status,
            updated_symbols=updated_symbols,
            failures=failures,
            exchange_status=exchange_status,
        )
        await self._save_portfolio(update_history=status == "success")
        self._print_update_statistics(us_stocks_count, local_stocks_count, original_portfolio)

        return UpdateResult(
            status=status,
            updated_symbols=updated_symbols,
            failed_symbols=[failure.to_status_dict() for failure in failures],
        )

    def _ordered_failures(self, symbols_to_update, batch):
        failures = []
        for symbol in symbols_to_update:
            if symbol in batch.prices:
                continue
            failures.append(
                batch.failures.get(
                    symbol,
                    PriceFailure(
                        symbol=symbol,
                        reason="price_unavailable",
                        message="No provider returned a valid price",
                    ),
                )
            )
        return failures

    def _build_update_status(
        self,
        status,
        updated_symbols,
        failures,
        exchange_status,
        message=None,
    ):
        update_status = {
            "status": status,
            "retrieved_at": get_current_timestamp(),
            "updatedSymbols": updated_symbols,
            "failedSymbols": [failure.to_status_dict() for failure in failures],
            "exchangeRate": exchange_status,
        }
        if message:
            update_status["message"] = message
        return update_status

    def _update_portfolio_calculations(self):
        """更新投資組合計算"""
        total_value_twd = self._calculate_total_value()
        old_total = self.portfolio['totalValue']

        if abs(total_value_twd - old_total) > 0.01:
            print("\n重新計算投資組合:")
            print(f"- 原總值: TWD {old_total:,.2f}")
            print(f"- 新總值: TWD {total_value_twd:,.2f}")

        self.portfolio['totalValue'] = total_value_twd
        exchange_rate = float(self.portfolio['exchange rate'])

        for stock in self.portfolio['stocks']:
            value_twd = stock['price'] * stock['quantity']
            if stock['currency'] == 'USD':
                value_twd *= exchange_rate
            stock['percentageOfTotal'] = round((value_twd / total_value_twd) * 100, 2)

    def _print_update_statistics(self, us_stocks_count, local_stocks_count, original_portfolio):
        if us_stocks_count <= 0 and local_stocks_count <= 0:
            return

        print("\n更新統計:")
        if us_stocks_count > 0:
            print(f"- 更新了 {us_stocks_count} 支美股價格（收盤價）")
        if local_stocks_count > 0:
            print(f"- 更新了 {local_stocks_count} 支台股價格")
        print(
            f"- 投資組合總值變動: "
            f"TWD {original_portfolio['totalValue']:,.2f} → TWD {self.portfolio['totalValue']:,.2f}"
        )

        print("\n投資佔比統計:")
        sorted_stocks = sorted(
            self.portfolio['stocks'],
            key=lambda x: x['percentageOfTotal'],
            reverse=True,
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
