import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    """應用程式配置類別"""
    BASE_URL: str = "https://www.google.com/finance/quote/"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    TIMEZONE: str = "Asia/Taipei"
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

def setup_logging(config: Config) -> logging.Logger:
    """
    設置日誌配置
    
    Args:
        config (Config): 配置物件
    
    Returns:
        logging.Logger: 配置完成的日誌記錄器
    """
    # 創建日誌目錄
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)

    # 設定根日誌記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # 設定第三方庫的日誌層級
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

    # 配置控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)

    # 配置檔案處理器
    log_filename = os.path.join(
        config.LOG_DIR,
        f'stocktracker_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # 清除現有的處理器
    root_logger.handlers.clear()
    
    # 添加新的處理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 建立應用程式日誌記錄器
    logger = logging.getLogger('StockTracker')
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    return logger

def get_config() -> Config:
    """
    載入設定
    
    Returns:
        Config: 設定物件
    """
    load_dotenv()
    
    return Config(
        BASE_URL=os.getenv("BASE_URL", Config.BASE_URL),
        USER_AGENT=os.getenv("USER_AGENT", Config.USER_AGENT),
        TIMEZONE=os.getenv("TIMEZONE", Config.TIMEZONE),
        LOG_LEVEL=os.getenv("LOG_LEVEL", Config.LOG_LEVEL),
        LOG_DIR=os.getenv("LOG_DIR", Config.LOG_DIR),
        LOG_MAX_BYTES=int(os.getenv("LOG_MAX_BYTES", Config.LOG_MAX_BYTES)),
        LOG_BACKUP_COUNT=int(os.getenv("LOG_BACKUP_COUNT", Config.LOG_BACKUP_COUNT)),
    )

# 初始化配置和日誌
config = get_config()
logger = setup_logging(config)