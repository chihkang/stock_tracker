# src/stock_tracker/gist_utils.py
import aiohttp
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

HISTORY_FILENAME = 'portfolio-history.json'

class GistManager:
    def __init__(self, gist_id, token):
        self.gist_id = gist_id
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/gists/{gist_id}'

    async def read_portfolio(self):
        """從 Gist 讀取 portfolio.json"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        gist_data = await response.json()
                        portfolio_content = gist_data['files']['portfolio.json']['content']
                        return json.loads(portfolio_content)
                    else:
                        logger.error(f"從 Gist 讀取失敗: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"從 Gist 讀取失敗: {str(e)}")
            return None

    async def read_history(self):
        """從 Gist 讀取 portfolio-history.json；檔案不存在時回傳空歷史。"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        gist_data = await response.json()
                        history_file = gist_data.get('files', {}).get(HISTORY_FILENAME)
                        if not history_file:
                            return {'values': []}
                        return json.loads(history_file.get('content') or '{"values": []}')
                    else:
                        logger.error(f"從 Gist 讀取歷史檔失敗: {response.status}")
                        return {'values': []}
        except Exception as e:
            logger.error(f"從 Gist 讀取歷史檔失敗: {str(e)}")
            return {'values': []}

    async def update_portfolio(self, portfolio_data, history_data=None):
        """更新 Gist 中的 portfolio.json，必要時同步 portfolio-history.json"""
        try:
            files = {
                'portfolio.json': {
                    'content': json.dumps(portfolio_data, indent=2, ensure_ascii=False)
                }
            }
            if history_data is not None:
                files[HISTORY_FILENAME] = {
                    'content': json.dumps(history_data, indent=2, ensure_ascii=False)
                }

            payload = {
                'files': files
            }
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.patch(self.base_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("已成功更新 Gist 中的 portfolio.json")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"更新 Gist 失敗: {response.status}, {response_text}")
                        return False
        except Exception as e:
            logger.error(f"更新 Gist 失敗: {str(e)}")
            return False

    async def create_backup(self, portfolio_data, backup_dir='backups'):
        """建立本地備份"""
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'portfolio_{timestamp}.json')
            
            # 寫入檔案操作不需要非同步，因為是本地操作
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已建立備份: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"建立備份失敗: {str(e)}")
            return False
