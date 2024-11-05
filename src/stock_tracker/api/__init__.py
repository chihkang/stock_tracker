from .client import PortfolioApiClient

__all__ = ['PortfolioApiClient', 'get_api_client']

_api_client_instance = None

def get_api_client() -> PortfolioApiClient:
    """
    取得 API 客戶端的單例實例
    
    Returns:
        PortfolioApiClient: API 客戶端實例
    """
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = PortfolioApiClient()
    return _api_client_instance