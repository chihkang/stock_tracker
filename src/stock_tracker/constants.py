from datetime import time

# URL相關
GOOGLE_FINANCE_BASE_URL = "https://www.google.com/finance/quote/"

# 使用者代理
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# 時區設定
DEFAULT_TIMEZONE = "Asia/Taipei"

# HTTP 請求相關
REQUEST_TIMEOUT = 10  # 秒
MAX_RETRIES = 3

# 輸出格式相關
TABLE_WIDTH = 80
COLUMN_WIDTHS = {
    "symbol": 15,
    "price": 15,
    "timestamp": 30
}

# 支援的交易所列表
SUPPORTED_EXCHANGES = {
    "NASDAQ": "NASDAQ",
    "NYSE": "NYSE",
    "NYSEARCA": "NYSEARCA",
    "TPE": "TPE",  # 台灣證券交易所
    "TWSE": "TWSE",  # 另一種台灣證交所代號
    "HKG": "HKG",  # 香港交易所
    "SHA": "SHA",  # 上海證券交易所
    "SHE": "SHE",  # 深圳證券交易所
    "TYO": "TYO",  # 東京證券交易所
}

# 貨幣代碼
CURRENCIES = {
    "USD": "$",
    "TWD": "NT$",
    "HKD": "HK$",
    "CNY": "¥",
    "JPY": "¥",
}

# 錯誤訊息
ERROR_MESSAGES = {
    "invalid_symbol": "無效的股票代號格式: {symbol}",
    "unsupported_exchange": "不支援的交易所: {exchange}",
    "network_error": "網路連線錯誤: {error}",
    "parse_error": "解析錯誤: {error}",
    "timeout_error": "請求超時: {error}",
}

# 日期時間格式
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# 定義市場交易時間
MARKET_HOURS = {
    'TPE': {  # 台灣證券交易所
        'timezone': 'Asia/Taipei',
        'trading_days': range(0, 5),  # 0=週一 到 4=週五
        'trading_hours': {
            'start': time(9, 0),
            'end': time(13, 30)
        }
    },
    'TWO': {  # 台灣櫃買中心
        'timezone': 'Asia/Taipei',
        'trading_days': range(0, 5),
        'trading_hours': {
            'start': time(9, 0),
            'end': time(13, 30)
        }
    },
    'NASDAQ': {  # 納斯達克（動態計算，此處時間僅作參考）
        'timezone': 'Asia/Taipei',
        'trading_days': range(0, 5),
        'description': '美東時間 09:30-16:00 (台灣時間根據夏令時間自動調整)'
    }
}

# 市場代碼映射
MARKET_MAPPING = {
    'TPE': 'TPE',
    'TWO': 'TWO',
    'NASDAQ': 'NASDAQ',
    'NYSE': 'NASDAQ',
    'NYSEARCA': 'NASDAQ'
}