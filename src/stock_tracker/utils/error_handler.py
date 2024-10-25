import sys
import traceback
import logging
from functools import wraps
from pathlib import Path
from datetime import datetime

def setup_logging():
    """設置日誌系統"""
    # 確保日誌目錄存在
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # 生成日誌檔案名稱，包含日期
    current_date = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f'stocktracker_{current_date}.log'
    
    # 配置日誌
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('StockTracker')
    logger.setLevel(logging.DEBUG)
    
    return logger

def error_handler(func):
    """錯誤處理裝飾器"""
    logger = setup_logging()
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 記錄詳細的錯誤資訊
            error_msg = f"錯誤: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            
            # 如果是在凍結的執行檔中執行
            if getattr(sys, 'frozen', False):
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showerror(
                        "錯誤",
                        f"程式發生錯誤:\n{str(e)}\n\n"
                        f"詳細日誌已儲存到:\n{logger.handlers[0].baseFilename}"
                    )
                except:
                    pass  # 如果無法顯示GUI錯誤訊息，就忽略
            
            # 簡化的錯誤訊息輸出到控制台
            print(f"\n錯誤: {str(e)}", file=sys.stderr)
            print(f"詳細日誌已儲存到: {logger.handlers[0].baseFilename}", file=sys.stderr)
            
            return 1  # 返回錯誤代碼
    
    return wrapper

def log_execution_time(func):
    """記錄函數執行時間的裝飾器"""
    logger = logging.getLogger('StockTracker')
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            execution_time = datetime.now() - start_time
            logger.debug(f"函數 {func.__name__} 執行時間: {execution_time}")
            return result
        except Exception as e:
            execution_time = datetime.now() - start_time
            logger.error(f"函數 {func.__name__} 執行失敗，耗時: {execution_time}")
            raise
    
    return wrapper