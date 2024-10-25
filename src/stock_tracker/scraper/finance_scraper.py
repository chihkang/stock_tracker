import requests
from bs4 import BeautifulSoup
from ..exceptions import ScraperError
from ..utils.time_utils import get_current_timestamp

def get_stock_price_from_google(symbol: str) -> dict:
    """從 Google Finance 獲取股價"""
    try:
        url = f"https://www.google.com/finance/quote/{symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.find('div', {'data-last-price': True})
        
        if not price_element:
            return None
            
        return {
            'price': float(price_element['data-last-price']),
            'timestamp': get_current_timestamp()
        }
            
    except Exception:
        return None

def get_stock_price_from_yahoo(stock_id: str) -> dict:
    """從 Yahoo Finance 台灣獲取股價"""
    try:
        url = f"https://tw.stock.yahoo.com/quote/{stock_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找包含"成交"的元素
        price_items = soup.find_all('li', class_='price-detail-item')
        for item in price_items:
            label_span = item.find('span', string='成交')
            if label_span:
                # 獲取成交價格
                price_span = item.find_all('span')[-1]  # 取最後一個 span
                if price_span and price_span.text.strip():
                    try:
                        return {
                            'price': float(price_span.text.strip()),
                            'timestamp': get_current_timestamp()
                        }
                    except ValueError:
                        continue
        
        return None
            
    except Exception as e:
        print(f"Yahoo Finance 爬蟲錯誤: {str(e)}")
        return None

def format_yahoo_symbol(symbol: str) -> str:
    """將股票代號格式轉換為 Yahoo Finance 格式"""
    # 例如: "00687B:TWO" -> "00687B.TWO"
    if ':' in symbol:
        code, market = symbol.split(':')
        return f"{code}.{market}"
    return symbol

def get_stock_price(symbol: str) -> dict:
    """
    獲取股價，自動嘗試不同數據源
    
    Args:
        symbol: 股票代號 (例如: "00687B:TWO" 或 "2330:TPE")
        
    Returns:
        dict: 包含價格和時間戳的字典
    """
    # 先嘗試 Google Finance
    result = get_stock_price_from_google(symbol)
    if result:
        return result
        
    # Google 失敗則嘗試 Yahoo Finance
    yahoo_symbol = format_yahoo_symbol(symbol)
    result = get_stock_price_from_yahoo(yahoo_symbol)
    if result:
        return result
        
    raise ScraperError(f"無法從任何來源獲取 {symbol} 的價格")

def get_multiple_stock_prices(symbols: list) -> dict:
    """
    獲取多個股票的價格
    
    Args:
        symbols: 股票代號列表
        
    Returns:
        dict: 股票代號到價格信息的映射
    """
    results = {}
    for symbol in symbols:
        try:
            results[symbol] = get_stock_price(symbol)
        except ScraperError as e:
            print(f"警告: {str(e)}")
            continue
    return results