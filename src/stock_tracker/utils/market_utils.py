from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from ..constants import MARKET_HOURS, MARKET_MAPPING
from typing import Optional  # 添加這行


def get_market_from_symbol(symbol: str) -> str:
    """從股票代號取得市場代碼"""
    parts = symbol.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid symbol format: {symbol}")
    return MARKET_MAPPING.get(parts[1], parts[1])

def get_us_market_hours() -> tuple[time, time]:
    """
    根據當前日期判斷美股交易時間（考慮夏令時間）
    
    Returns:
        tuple[time, time]: (開盤時間, 收盤時間) 以台灣時間表示
    """
    # 獲取當前美東時間
    ny_tz = ZoneInfo('America/New_York')
    tw_tz = ZoneInfo('Asia/Taipei')
    
    # 獲取今天美東的 9:30 和 16:00
    ny_now = datetime.now(ny_tz)
    ny_market_open = ny_now.replace(hour=9, minute=30, second=0, microsecond=0)
    ny_market_close = ny_now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # 轉換到台灣時間
    tw_market_open = ny_market_open.astimezone(tw_tz)
    tw_market_close = ny_market_close.astimezone(tw_tz)
    
    # 返回時間物件
    return (tw_market_open.time(), tw_market_close.time())

def is_market_open(market: str, check_time: datetime = None) -> bool:
    """檢查指定市場在給定時間是否開市"""
    if market not in MARKET_HOURS:
        raise ValueError(f"Unknown market: {market}")
        
    market_config = MARKET_HOURS[market]
    market_tz = ZoneInfo(market_config['timezone'])
    
    # 如果沒有提供時間，使用當前時間
    if check_time is None:
        check_time = datetime.now(market_tz)
    elif check_time.tzinfo is None:
        check_time = check_time.replace(tzinfo=market_tz)
    else:
        check_time = check_time.astimezone(market_tz)
    
    # 檢查是否為交易日
    weekday = check_time.weekday()
    if weekday not in market_config['trading_days']:
        return False
    
    # 對於美股市場，動態獲取交易時間
    if market in ['NASDAQ', 'NYSE', 'NYSEARCA']:
        market_open, market_close = get_us_market_hours()
        current_time = check_time.time()
        
        # 處理跨日情況
        if market_close < market_open:  # 跨日交易
            return current_time >= market_open or current_time <= market_close
        else:
            return market_open <= current_time <= market_close
    
    # 其他市場使用固定時間
    else:
        trading_start = market_config['trading_hours']['start']
        trading_end = market_config['trading_hours']['end']
        current_time = check_time.time()
        
        return trading_start <= current_time <= trading_end

def should_update_price(symbol: str, last_updated: Optional[str] = None, force_update: bool = False) -> bool:
    """
    判斷是否應該更新股票價格
    
    Args:
        symbol (str): 股票代號
        last_updated (str, optional): 上次更新時間
        force_update (bool): 是否強制更新，若為True則忽略時間限制直接更新
    
    Returns:
        bool: 是否需要更新
    """
    # 如果強制更新模式開啟，直接返回True
    if force_update:
        return True
        
    if not last_updated:
        return True
        
    market = get_market_from_symbol(symbol)
    
    # 如果市場開盤中，則需要更新
    if is_market_open(market):
        return True
    
    # 解析上次更新時間
    try:
        # 假設時間戳格式為 ISO 格式
        last_update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        
        # 如果超過24小時沒更新，則需要更新
        if (current_time - last_update_time).total_seconds() > 24 * 60 * 60:
            return True
            
    except (ValueError, AttributeError) as e:
        logger.warning(f"解析更新時間失敗: {str(e)}")
        return True
    
    return False

def format_market_hours(market: str) -> str:
    """
    格式化顯示市場交易時間
    """
    if market in ['NASDAQ', 'NYSE', 'NYSEARCA']:
        market_open, market_close = get_us_market_hours()
        return f"{market_open.strftime('%H:%M')}-{market_close.strftime('%H:%M')} (台灣時間)"
    else:
        market_config = MARKET_HOURS[market]
        start = market_config['trading_hours']['start']
        end = market_config['trading_hours']['end']
        return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"