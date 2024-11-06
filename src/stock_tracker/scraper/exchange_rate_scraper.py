import requests
from bs4 import BeautifulSoup
from ..exceptions import ScraperError
import asyncio
from ..exceptions import ScraperError

async def update_exchange_rate(currency_pair='USD-TWD'):
    """
    從 Google Finance 獲取匯率並更新到 API
    
    Args:
        currency_pair: 貨幣對，例如 'USD-TWD'
    
    Returns:
        float: 匯率（四捨五入到小數點後兩位）
    """
    try:
        # 獲取匯率
        rate = get_exchange_rate(currency_pair)        
        return rate
            
    except Exception as e:
        raise ScraperError(f"獲取匯率時發生錯誤: {str(e)}")

def get_exchange_rate(currency_pair='USD-TWD'):
    """
    從 Google Finance 獲取匯率
    
    Args:
        currency_pair: 貨幣對，例如 'USD-TWD'
    
    Returns:
        float: 匯率（四捨五入到小數點後兩位）
    """
    try:
        url = f"https://www.google.com/finance/quote/{currency_pair}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rate_element = soup.find('div', {'data-last-price': True})
        
        if not rate_element:
            raise ScraperError(f"無法找到 {currency_pair} 的匯率資訊")
            
        # 將匯率四捨五入到小數點後兩位
        exchange_rate = round(float(rate_element['data-last-price']), 2)
        return exchange_rate
            
    except requests.RequestException as e:
        raise ScraperError(f"請求匯率資訊時發生錯誤: {str(e)}")
    except (ValueError, AttributeError) as e:
        raise ScraperError(f"解析匯率資訊時發生錯誤: {str(e)}")
    except Exception as e:
        raise ScraperError(f"獲取匯率時發生未預期的錯誤: {str(e)}")