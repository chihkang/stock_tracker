import sys
import argparse
from .scraper.finance_scraper import get_multiple_stock_prices
from .formatters.console_formatter import format_output
from .portfolio.portfolio_manager import PortfolioManager
from .exceptions import StockTrackerError

def parse_arguments() -> argparse.Namespace:
    """解析命令列參數"""
    parser = argparse.ArgumentParser(description='股票價格追蹤器')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 查詢股票價格命令
    query_parser = subparsers.add_parser('query', help='查詢股票價格')
    query_parser.add_argument('symbols', nargs='+', help='股票代號列表')
    
    # 更新投資組合命令
    portfolio_parser = subparsers.add_parser('portfolio', help='更新投資組合')
    portfolio_parser.add_argument('--file', default='portfolio.json', help='投資組合檔案路徑')
    
    return parser.parse_args()

def main(args: list = None) -> int:
    """主程式進入點"""
    if args is None:
        args = sys.argv[1:]
    
    try:
        args = parse_arguments()
        
        if args.command == 'query':
            # 查詢股票價格
            prices = get_multiple_stock_prices(args.symbols)
            format_output(prices)
        elif args.command == 'portfolio':
            # 更新投資組合
            portfolio = PortfolioManager(args.file)
            portfolio.update_prices()
            portfolio.print_portfolio()
        else:
            print("請指定命令: query 或 portfolio")
            return 1
            
        return 0
        
    except StockTrackerError as e:
        print(f"錯誤: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"未預期的錯誤: {str(e)}", file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())