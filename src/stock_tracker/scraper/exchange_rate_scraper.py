import requests
from ..exceptions import ScraperError
from ..constants import DEFAULT_USER_AGENT, REQUEST_TIMEOUT


class ExchangeRateService:
    async def get_rate(self, currency_pair='USD-TWD'):
        return await update_exchange_rate(currency_pair)

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
    從免 API key 的公開 JSON 匯率服務獲取匯率
    
    Args:
        currency_pair: 貨幣對，例如 'USD-TWD'
    
    Returns:
        float: 匯率（四捨五入到小數點後兩位）
    """
    try:
        base_currency, target_currency = _split_currency_pair(currency_pair)
        url = f"https://open.er-api.com/v6/latest/{base_currency}"

        headers = {'User-Agent': DEFAULT_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        if data.get("result") != "success":
            raise ScraperError(f"匯率服務回應失敗: {data.get('result')}")

        rates = data.get("rates") or {}
        if target_currency not in rates:
            raise ScraperError(f"無法找到 {currency_pair} 的匯率資訊")

        # 將匯率四捨五入到小數點後兩位
        exchange_rate = round(float(rates[target_currency]), 2)
        return exchange_rate

    except requests.RequestException as e:
        raise ScraperError(f"請求匯率資訊時發生錯誤: {str(e)}")
    except (ValueError, AttributeError, KeyError) as e:
        raise ScraperError(f"解析匯率資訊時發生錯誤: {str(e)}")
    except Exception as e:
        raise ScraperError(f"獲取匯率時發生未預期的錯誤: {str(e)}")


def _split_currency_pair(currency_pair):
    parts = currency_pair.split("-")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid currency pair: {currency_pair}")
    return parts[0].upper(), parts[1].upper()
