class StockTrackerError(Exception):
    """股票追蹤器基礎例外類別"""
    pass

class ScraperError(StockTrackerError):
    """爬蟲相關錯誤"""
    pass

class ValidationError(StockTrackerError):
    """資料驗證錯誤"""
    pass

class ConfigurationError(StockTrackerError):
    """設定相關錯誤"""
    pass

class FormattingError(StockTrackerError):
    """輸出格式化錯誤"""
    pass