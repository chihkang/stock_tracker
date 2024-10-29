import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from .gist_utils import GistManager
from .portfolio.portfolio_manager import PortfolioManager
from .utils.error_handler import error_handler

def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"stocktracker_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

@error_handler
def main():
    parser = argparse.ArgumentParser(description='股票投資組合管理工具')
    parser.add_argument('command', choices=['portfolio'], help='執行的命令')
    parser.add_argument('--file', default='portfolio.json', help='投資組合檔案路徑')
    
    args = parser.parse_args()
    logger = setup_logging()
    
    if args.command == 'portfolio':
        # 檢查環境變數
        gist_id = os.environ.get('GIST_ID')
        gist_token = os.environ.get('GIST_TOKEN')
        
        if gist_id and gist_token:
            logger.info("使用 Gist 模式")
            gist_manager = GistManager(gist_id, gist_token)
            portfolio_manager = PortfolioManager(file_path=args.file, gist_manager=gist_manager)
        else:
            # 檢查本地文件是否存在
            if not os.path.exists(args.file):
                raise FileNotFoundError(f"找不到必要的配置文件: {args.file}")
            logger.info("使用本地檔案模式")
            portfolio_manager = PortfolioManager(file_path=args.file)
        
        portfolio_manager.update_prices()
        portfolio_manager.print_portfolio()
        
    return 0

if __name__ == '__main__':
    sys.exit(main())