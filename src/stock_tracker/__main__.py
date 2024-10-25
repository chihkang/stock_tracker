import sys
import os
import argparse
from stock_tracker.utils.error_handler import error_handler, setup_logging
from stock_tracker.portfolio.portfolio_manager import PortfolioManager
from stock_tracker.scraper.finance_scraper import get_multiple_stock_prices
from stock_tracker.formatters.console_formatter import format_output

logger = setup_logging()

def parse_arguments():
    parser = argparse.ArgumentParser(description='股票價格追蹤器')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    query_parser = subparsers.add_parser('query', help='查詢股票價格')
    query_parser.add_argument('symbols', nargs='+', help='股票代號列表')
    
    portfolio_parser = subparsers.add_parser('portfolio', help='更新投資組合')
    portfolio_parser.add_argument('--file', default='portfolio.json', help='投資組合檔案路徑')
    portfolio_parser.add_argument('--charts', action='store_true', help='生成視覺化圖表')
    portfolio_parser.add_argument('--output-dir', default='plots', help='圖表輸出目錄')
    
    return parser.parse_args()

@error_handler
def main(args=None):
    logger.info("程式啟動")
    
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.dirname(sys.executable)
        logger.info(f"Bundle 目錄: {bundle_dir}")
        
        if sys.platform == 'darwin':
            if '.app' in bundle_dir:
                bundle_dir = os.path.dirname(os.path.dirname(bundle_dir))
        
        os.chdir(bundle_dir)
        logger.info(f"工作目錄已切換至: {os.getcwd()}")
    
    try:
        if args is None:
            args = parse_arguments()
        
        logger.info(f"執行命令: {args.command}")
            
        if args.command == 'query':
            logger.info(f"查詢股票: {args.symbols}")
            prices = get_multiple_stock_prices(args.symbols)
            format_output(prices)
            
        elif args.command == 'portfolio':
            if not os.path.exists(args.file):
                logger.error(f"找不到配置文件: {args.file}")
                raise FileNotFoundError(f"找不到必要的配置文件: {args.file}")
            
            logger.info(f"載入投資組合: {args.file}")
            portfolio = PortfolioManager(args.file)
            
            try:
                portfolio.update_prices()
                portfolio.print_portfolio()
                
                if args.charts:
                    logger.info("生成視覺化圖表")
                    try:
                        import matplotlib
                        portfolio.generate_charts(args.output_dir)
                        logger.info(f"圖表已生成在 {args.output_dir} 目錄")
                    except ImportError:
                        logger.error("未安裝 matplotlib，無法生成圖表")
                        print("\n請安裝必要套件：pip install matplotlib")
                        return 1
                    except Exception as e:
                        logger.error(f"生成圖表時發生錯誤: {str(e)}")
                        print(f"\n生成圖表時發生錯誤: {str(e)}")
                        return 1
                
            except Exception as e:
                logger.error(f"更新投資組合時發生錯誤: {str(e)}")
                raise
        else:
            logger.error("未指定有效的命令")
            print("請指定命令: query 或 portfolio")
            return 1
            
        return 0
        
    except KeyboardInterrupt:
        logger.info("使用者中斷執行")
        return 130
    except Exception as e:
        logger.error(f"執行時發生未預期的錯誤: {str(e)}")
        raise
    finally:
        logger.info("程式結束")

if __name__ == '__main__':
    sys.exit(main())