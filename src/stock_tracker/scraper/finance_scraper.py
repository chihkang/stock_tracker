# src/stock_tracker/scraper/finance_scraper.py
import logging
import aiohttp
from ..exceptions import ScraperError
from ..api import get_api_client
from bs4 import BeautifulSoup
import requests
from ..utils.time_utils import get_current_timestamp

logger = logging.getLogger(__name__)

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
        logger.error(f"Yahoo Finance 爬蟲錯誤: {str(e)}")
        return None

def format_yahoo_symbol(symbol: str) -> str:
    """將股票代號格式轉換為 Yahoo Finance 格式"""
    if ':' in symbol:
        code, market = symbol.split(':')
        return f"{code}.{market}"
    return symbol

def get_stock_price(symbol: str) -> dict:
    """
    獲取股價，自動嘗試不同數據源
    
    Args:
        symbol: 股票代號
        
    Returns:
        dict: 包含價格和時間戳的字典
    """
    try:
        # 先嘗試 Google Finance
        result = get_stock_price_from_google(symbol)
        if result:
            logger.info(f"從 Google Finance 成功獲取 {symbol} 價格")
            return result
            
        # Google 失敗則嘗試 Yahoo Finance
        yahoo_symbol = format_yahoo_symbol(symbol)
        result = get_stock_price_from_yahoo(yahoo_symbol)
        if result:
            logger.info(f"從 Yahoo Finance 成功獲取 {symbol} 價格")
            return result
            
        logger.error(f"無法從任何來源獲取 {symbol} 的價格")
        raise ScraperError(f"無法從任何來源獲取 {symbol} 的價格")
        
    except Exception as e:
        logger.error(f"獲取價格時發生錯誤: {str(e)}")
        raise ScraperError(f"獲取價格時發生錯誤: {str(e)}")

async def update_stock_price(symbol: str) -> dict:
    """
    獲取股價並更新到 API
    
    Args:
        symbol: 股票代號
        
    Returns:
        dict: 包含價格和時間戳的字典
    """
    try:
        # 獲取股價
        price_info = get_stock_price(symbol)
        
        if price_info:
            # 更新到 API
            api_client = get_api_client()
            success = await api_client.update_stock_price(symbol, price_info['price'])
            
            if not success:
                logger.warning(f"股票 {symbol} 價格更新到 API 失敗")
                
            return price_info
            
    except Exception as e:
        logger.error(f"更新股票價格時發生錯誤: {str(e)}")
        raise ScraperError(f"獲取股票 {symbol} 的價格時發生錯誤: {str(e)}")

def get_multiple_stock_prices(symbols: list) -> dict:
    """
    同步獲取多個股票的價格
    """
    results = {}
    for symbol in symbols:
        try:
            result = get_stock_price(symbol)
            if result:
                results[symbol] = result
        except ScraperError as e:
            logger.error(f"警告: {str(e)}")
            continue
    return results

async def update_multiple_stock_prices(symbols: list) -> dict:
    """
    獲取多個股票的價格並更新到 API
    
    Args:
        symbols: 股票代號列表
        
    Returns:
        dict: 股票代號到價格信息的映射
    """
    results = {}
    for symbol in symbols:
        try:
            result = await update_stock_price(symbol)
            if result:
                results[symbol] = result
        except ScraperError as e:
            logger.error(f"警告: {str(e)}")
            continue
    return results

# 明確列出可以被匯入的名稱
__all__ = ['get_stock_price', 'get_multiple_stock_prices', 'update_stock_price', 'update_multiple_stock_prices']