import os
import logging
from datetime import datetime
from pathlib import Path
from .gist_utils import GistManager
from .portfolio.portfolio_manager import PortfolioManager

# 設定日誌
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

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 從環境變數獲取 Gist 設定
        gist_id = os.environ.get('GIST_ID')
        gist_token = os.environ.get('GIST_TOKEN')
        
        if not gist_id or not gist_token:
            logger.warning("未設定 GIST_ID 或 GIST_TOKEN，將只使用本地檔案")
            portfolio_manager = PortfolioManager()
        else:
            # 初始化 GistManager
            gist_manager = GistManager(gist_id, gist_token)
            logger.info("已初始化 GistManager")
            
            # 初始化 PortfolioManager，傳入 GistManager 實例
            portfolio_manager = PortfolioManager(gist_manager=gist_manager)
            logger.info("已初始化 PortfolioManager with GistManager")
        
        # 更新投資組合
        portfolio_manager.update_prices()
        
        # 顯示更新後的投資組合
        portfolio_manager.print_portfolio()
        
        logger.info("投資組合更新完成")
        
    except Exception as e:
        logger.error(f"更新過程發生錯誤: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()