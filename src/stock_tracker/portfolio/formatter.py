from prettytable import PrettyTable, PLAIN_COLUMNS
from ..utils.market_utils import format_market_hours

class PortfolioFormatter:
    """處理所有輸出格式化相關的功能"""
    
    @staticmethod
    def create_table():
        """創建並配置表格"""
        table = PrettyTable()
        table.set_style(PLAIN_COLUMNS)
        table.field_names = ["股票代號", "價格", "數量", "總值 (TWD)", "比例", "更新時間"]
        
        # 設置對齊和寬度
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
        return table

    @staticmethod
    def print_market_status(market_status):
        """顯示市場狀態"""
        print("\n市場狀態:")
        for market, is_open in market_status.items():
            trading_hours = format_market_hours(market)
            status = "交易中" if is_open else "收盤中"
            if market in ['NASDAQ', 'NYSE', 'NYSEARCA'] and not is_open:
                status += " (使用最新收盤價)"
            print(f"{market}: {trading_hours} - {status}")

    @staticmethod
    def print_update_summary(update_count, old_total, new_total):
        """打印更新摘要"""
        print("\n更新統計:")
        if update_count['us'] > 0:
            print(f"- 更新了 {update_count['us']} 支美股價格（收盤價）")
        if update_count['local'] > 0:
            print(f"- 更新了 {update_count['local']} 支台股價格")
        if abs(new_total - old_total) > 0.01:
            print(f"- 投資組合總值變動: TWD {old_total:,.2f} → TWD {new_total:,.2f}")