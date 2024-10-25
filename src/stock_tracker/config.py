import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    BASE_URL: str = "https://www.google.com/finance/quote/"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    TIMEZONE: str = "Asia/Taipei"

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
    )