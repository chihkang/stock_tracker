# src/stock_tracker/scraper/finance_scraper.py
import logging

from ..api import get_api_client
from ..exceptions import ScraperError
from ..providers.market_data import MarketDataService, PriceFailure

logger = logging.getLogger(__name__)


def _run_async(coro):
    import asyncio

    return asyncio.run(coro)


def get_stock_price(symbol: str) -> dict:
    """
    獲取股價，自動依市場代號路由到對應資料來源。
    """
    try:
        batch = _run_async(MarketDataService().get_prices([symbol]))
        if symbol in batch.prices:
            logger.info("成功獲取 %s 價格", symbol)
            return batch.prices[symbol].to_legacy_dict()

        failure = batch.failures.get(symbol)
        message = failure.message if failure else "No provider returned a valid price"
        raise ScraperError(message)
    except ScraperError:
        raise
    except Exception as exc:
        logger.error("獲取價格時發生錯誤: %s", exc)
        raise ScraperError(f"獲取價格時發生錯誤: {exc}")


async def update_stock_price(symbol: str) -> dict:
    """
    獲取股價並更新到外部 Portfolio API。API 更新失敗只記錄警告，維持既有容錯行為。
    """
    batch = await MarketDataService().get_prices([symbol])
    if symbol in batch.failures:
        failure = batch.failures[symbol]
        raise ScraperError(failure.message or failure.reason)

    price_info = batch.prices[symbol].to_legacy_dict()
    api_client = get_api_client()
    success = await api_client.update_stock_price(symbol, price_info["price"])
    if not success:
        logger.warning("股票 %s 價格更新到 API 失敗", symbol)
    return price_info


def get_multiple_stock_prices(symbols: list) -> dict:
    """
    同步獲取多個股票的價格，保留舊 public API 的 dict 回傳格式。
    """
    results = {}
    batch = _run_async(MarketDataService().get_prices(symbols))
    for symbol, result in batch.prices.items():
        results[symbol] = result.to_legacy_dict()
    for failure in batch.failures.values():
        logger.error("警告: %s %s", failure.symbol, failure.message or failure.reason)
    return results


async def update_multiple_stock_prices(symbols: list) -> dict:
    """
    獲取多個股票價格並嘗試同步到外部 Portfolio API。
    """
    results = {}
    batch = await MarketDataService().get_prices(symbols)
    api_client = get_api_client()

    for symbol, result in batch.prices.items():
        price_info = result.to_legacy_dict()
        success = await api_client.update_stock_price(symbol, price_info["price"])
        if not success:
            logger.warning("股票 %s 價格更新到 API 失敗", symbol)
        results[symbol] = price_info

    for failure in batch.failures.values():
        logger.error("警告: %s %s", failure.symbol, failure.message or failure.reason)

    return results


__all__ = [
    "get_stock_price",
    "get_multiple_stock_prices",
    "update_stock_price",
    "update_multiple_stock_prices",
]
