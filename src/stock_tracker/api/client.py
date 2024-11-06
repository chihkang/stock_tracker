# src/stock_tracker/api/client.py
import aiohttp
import logging
import json
from typing import Optional
from ..config import config

logger = logging.getLogger(__name__)

class PortfolioApiClient:
    def __init__(self, base_url: str = config.PORTFOLIO_API_URL):
        """初始化 API 客戶端"""
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json'
        }
        logger.info(f"API Client initialized with base URL: {base_url}")
            
    async def update_stock_price(self, stock_name: str, new_price: float) -> bool:
        """更新股票價格"""
        url = f"{self.base_url}/api/Stock/name/{stock_name}/price"
        
        try:
            # logger.info(f"準備發送請求到: {url}")
            # logger.info(f"請求內容: {json.dumps(new_price, ensure_ascii=False)}")
            # logger.info(f"Headers: {json.dumps(self.headers, ensure_ascii=False)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=new_price) as response:
                    response_text = await response.text()
                    # logger.info(f"收到回應狀態碼: {response.status}")
                    # logger.info(f"收到回應內容: {response_text}")
                    
                    if response.status == 200:
                        logger.info(f"已成功更新股票 {stock_name} 的價格")
                        return True
                    else:
                        logger.error(f"更新股票 {stock_name} 的價格失敗。狀態碼: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"更新股票價格時發生錯誤: {str(e)}")
            return False
