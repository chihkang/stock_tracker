# src/stock_tracker/__main__.py
import os
import sys
import argparse
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from .gist_utils import GistManager
from .portfolio.portfolio_manager import PortfolioManager
from .utils.error_handler import error_handler

def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"stocktracker_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 設定 root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # 輸出到 stdout
        ]
    )
    logger = logging.getLogger(__name__)
    return logger

@error_handler
async def async_main():
    parser = argparse.ArgumentParser(description='股票投資組合管理工具')
    parser.add_argument('command', choices=['portfolio'], help='執行的命令')
    parser.add_argument('--file', default='portfolio.json', help='投資組合檔案路徑')
    parser.add_argument('--debug', action='store_true', help='啟用除錯模式')
    parser.add_argument('-f', '--force', action='store_true', 
                       help='強制更新所有股票價格，忽略更新時間限制')
    
    args = parser.parse_args()
    logger = setup_logging()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"GIST_ID environment variable: {'set' if os.environ.get('GIST_ID') else 'not set'}")
        logger.debug(f"GIST_TOKEN environment variable: {'set' if os.environ.get('GIST_TOKEN') else 'not set'}")

    if args.command == 'portfolio':
        # 檢查環境變數
        gist_id = os.environ.get('GIST_ID')
        gist_token = os.environ.get('GIST_TOKEN')

        if gist_id and gist_token:
            logger.info("使用 Gist 模式")
            try:
                gist_manager = GistManager(gist_id, gist_token)
                portfolio_manager = PortfolioManager(
                    file_path=args.file,
                    gist_manager=gist_manager,
                    force_update=args.force  # 傳入強制更新參數
                )
                await portfolio_manager.initialize()
                logger.info("成功初始化 GistManager 和 PortfolioManager")
            except Exception as e:
                logger.error(f"初始化 Gist 管理器失敗: {str(e)}")
                raise
        else:
            logger.info("使用本地檔案模式")
            if not os.path.exists(args.file):
                logger.error(f"找不到檔案: {args.file}")
                raise FileNotFoundError(f"找不到必要的配置文件: {args.file}")
            
            portfolio_manager = PortfolioManager(
                file_path=args.file,
                force_update=args.force  # 傳入強制更新參數
            )
            await portfolio_manager.initialize()

        # 使用 await 調用非同步方法
        if args.force:
            logger.info("強制更新模式已啟用，將更新所有股票價格")
        await portfolio_manager.update_prices()
        portfolio_manager.print_portfolio()
        
        return 0

def main():
    """同步入口點，用於執行非同步主函數"""
    return asyncio.run(async_main())

if __name__ == '__main__':
    sys.exit(main())