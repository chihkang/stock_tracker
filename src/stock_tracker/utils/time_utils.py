from datetime import datetime
import pytz
from ..constants import DEFAULT_TIMEZONE, DATETIME_FORMAT, ISO8601_FORMAT

def get_current_timestamp(timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    獲取當前時間戳記
    
    Args:
        timezone: 時區名稱，預設為 Asia/Taipei
    
    Returns:
        str: ISO8601 格式的時間戳記
    """
    tz = pytz.timezone(timezone)
    return datetime.now(tz).isoformat()

def format_timestamp(timestamp: str, format: str = DATETIME_FORMAT) -> str:
    """
    格式化時間戳記
    
    Args:
        timestamp: ISO8601 格式的時間戳記
        format: 輸出格式，預設為 DATETIME_FORMAT
        
    Returns:
        str: 格式化後的時間字串
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(format)
    except ValueError as e:
        return timestamp  # 如果解析失敗，返回原始字串

def convert_timezone(timestamp: str, target_timezone: str) -> str:
    """
    轉換時間戳記的時區
    
    Args:
        timestamp: ISO8601 格式的時間戳記
        target_timezone: 目標時區
        
    Returns:
        str: 轉換時區後的 ISO8601 時間戳記
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        target_tz = pytz.timezone(target_timezone)
        converted = dt.astimezone(target_tz)
        return converted.isoformat()
    except ValueError as e:
        return timestamp