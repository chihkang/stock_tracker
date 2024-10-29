import requests
import json
import os

class GistManager:
    def __init__(self, gist_id, token):
        self.gist_id = gist_id
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/gists/{gist_id}'

    def read_portfolio(self):
        """從 Gist 讀取 portfolio.json"""
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            gist_data = response.json()
            portfolio_content = gist_data['files']['portfolio.json']['content']
            return json.loads(portfolio_content)
        except Exception as e:
            print(f"從 Gist 讀取失敗: {str(e)}")
            return None

    def update_portfolio(self, portfolio_data):
        """更新 Gist 中的 portfolio.json"""
        try:
            payload = {
                'files': {
                    'portfolio.json': {
                        'content': json.dumps(portfolio_data, indent=2, ensure_ascii=False)
                    }
                }
            }
            
            response = requests.patch(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            print("已成功更新 Gist 中的 portfolio.json")
            return True
        except Exception as e:
            print(f"更新 Gist 失敗: {str(e)}")
            return False

    @staticmethod
    def create_backup(portfolio_data, backup_dir='backups'):
        """建立本地備份"""
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'portfolio_{timestamp}.json')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
            
            print(f"已建立備份: {backup_file}")
            return True
        except Exception as e:
            print(f"建立備份失敗: {str(e)}")
            return False