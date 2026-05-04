import logging
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from ..constants import DEFAULT_USER_AGENT, REQUEST_TIMEOUT
from ..utils.time_utils import get_current_timestamp

logger = logging.getLogger(__name__)


REASON_PRICE_UNAVAILABLE = "price_unavailable"
REASON_PROVIDER_HTTP_ERROR = "provider_http_error"
REASON_PROVIDER_PARSE_ERROR = "provider_parse_error"
REASON_UNSUPPORTED_SYMBOL = "unsupported_symbol"
REASON_RATE_UNAVAILABLE = "rate_unavailable"


@dataclass
class PriceResult:
    symbol: str
    price: float
    currency: str
    retrieved_at: str
    source: str
    market_timestamp: Optional[str] = None

    def to_legacy_dict(self) -> dict:
        return {
            "price": self.price,
            "currency": self.currency,
            "timestamp": self.retrieved_at,
            "source": self.source,
        }


@dataclass
class PriceFailure(Exception):
    symbol: str
    reason: str
    message: Optional[str] = None
    source: Optional[str] = None

    def __post_init__(self):
        Exception.__init__(self, self.message or self.reason)

    def to_status_dict(self) -> dict:
        status = {
            "symbol": self.symbol,
            "reason": self.reason,
        }
        if self.message:
            status["message"] = self.message
        return status


@dataclass
class PriceUpdateBatch:
    prices: Dict[str, PriceResult]
    failures: Dict[str, PriceFailure]


@dataclass
class ExchangeRateFailure(Exception):
    reason: str
    message: Optional[str] = None

    def __post_init__(self):
        Exception.__init__(self, self.message or self.reason)


def split_symbol(symbol: str) -> Tuple[str, str]:
    parts = symbol.split(":")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid symbol format: {symbol}")
    return parts[0], parts[1].upper()


def parse_price_text(value: str) -> float:
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned in {"-", "--", "N/A"}:
        raise ValueError("price is empty")
    return float(cleaned)


class BasePriceProvider:
    source = "BasePriceProvider"
    supported_exchanges: Tuple[str, ...] = ()

    def supports(self, symbol: str) -> bool:
        try:
            _, exchange = split_symbol(symbol)
        except ValueError:
            return False
        return exchange in self.supported_exchanges

    def normalize_symbol(self, symbol: str) -> str:
        raise NotImplementedError

    def fetch_price(self, symbol: str) -> PriceResult:
        raise NotImplementedError

    def _get_html(self, url: str) -> str:
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text


class YahooTaiwanProvider(BasePriceProvider):
    source = "YahooTaiwanProvider"
    supported_exchanges = ("TPE", "TWSE", "TWO")

    def normalize_symbol(self, symbol: str) -> str:
        code, exchange = split_symbol(symbol)
        suffix = "TWO" if exchange == "TWO" else "TW"
        return f"{code}.{suffix}"

    def fetch_price(self, symbol: str) -> PriceResult:
        yahoo_symbol = self.normalize_symbol(symbol)
        url = f"https://tw.stock.yahoo.com/quote/{yahoo_symbol}/"
        try:
            html = self._get_html(url)
            price = self._parse_price(html)
            return PriceResult(
                symbol=symbol,
                price=price,
                currency="TWD",
                retrieved_at=get_current_timestamp(),
                source=self.source,
            )
        except requests.RequestException as exc:
            logger.error("%s HTTP error for %s: %s", self.source, symbol, exc)
            raise PriceFailure(
                symbol=symbol,
                reason=REASON_PROVIDER_HTTP_ERROR,
                message=str(exc),
                source=self.source,
            )
        except (ValueError, AttributeError) as exc:
            logger.error("%s parse error for %s: %s", self.source, symbol, exc)
            raise PriceFailure(
                symbol=symbol,
                reason=REASON_PROVIDER_PARSE_ERROR,
                message=str(exc),
                source=self.source,
            )

    def _parse_price(self, html: str) -> float:
        soup = BeautifulSoup(html, "html.parser")
        price_items = soup.find_all(
            "li",
            class_=lambda value: value and "price-detail-item" in value.split(),
        )
        for item in price_items:
            label_span = item.find("span", string="成交")
            if label_span:
                spans = item.find_all("span")
                if spans:
                    return parse_price_text(spans[-1].get_text())
        raise ValueError("成交 price not found")


class YahooFinanceProvider(BasePriceProvider):
    source = "YahooFinanceProvider"
    supported_exchanges = ("NASDAQ", "NYSE", "NYSEARCA")

    def normalize_symbol(self, symbol: str) -> str:
        code, _ = split_symbol(symbol)
        return code

    def fetch_price(self, symbol: str) -> PriceResult:
        yahoo_symbol = self.normalize_symbol(symbol)
        url = f"https://finance.yahoo.com/quote/{yahoo_symbol}/"
        try:
            html = self._get_html(url)
            price = self._parse_price(html, yahoo_symbol)
            return PriceResult(
                symbol=symbol,
                price=price,
                currency="USD",
                retrieved_at=get_current_timestamp(),
                source=self.source,
            )
        except requests.RequestException as exc:
            logger.error("%s HTTP error for %s: %s", self.source, symbol, exc)
            raise PriceFailure(
                symbol=symbol,
                reason=REASON_PROVIDER_HTTP_ERROR,
                message=str(exc),
                source=self.source,
            )
        except (ValueError, AttributeError) as exc:
            logger.error("%s parse error for %s: %s", self.source, symbol, exc)
            raise PriceFailure(
                symbol=symbol,
                reason=REASON_PROVIDER_PARSE_ERROR,
                message=str(exc),
                source=self.source,
            )

    def _parse_price(self, html: str, yahoo_symbol: str) -> float:
        soup = BeautifulSoup(html, "html.parser")
        price_node = soup.find(attrs={"data-testid": "qsp-price"})
        if price_node and price_node.get_text(strip=True):
            return parse_price_text(price_node.get_text())

        streamer = soup.find(
            "fin-streamer",
            attrs={
                "data-symbol": yahoo_symbol,
                "data-field": "regularMarketPrice",
            },
        )
        if streamer and streamer.get_text(strip=True):
            return parse_price_text(streamer.get_text())

        match = re.search(r'"regularMarketPrice"\s*:\s*\{\s*"raw"\s*:\s*([0-9.]+)', html)
        if match:
            return float(match.group(1))

        raise ValueError("regular market price not found")


class MarketDataService:
    def __init__(self, providers: Optional[Iterable[BasePriceProvider]] = None):
        self.providers: List[BasePriceProvider] = list(
            providers
            if providers is not None
            else [
                YahooTaiwanProvider(),
                YahooFinanceProvider(),
            ]
        )

    def provider_for_symbol(self, symbol: str) -> BasePriceProvider:
        for provider in self.providers:
            if provider.supports(symbol):
                return provider
        raise PriceFailure(
            symbol=symbol,
            reason=REASON_UNSUPPORTED_SYMBOL,
            message=f"No provider supports {symbol}",
        )

    async def get_prices(self, symbols: Iterable[str]) -> PriceUpdateBatch:
        prices: Dict[str, PriceResult] = {}
        failures: Dict[str, PriceFailure] = {}

        for symbol in symbols:
            try:
                provider = self.provider_for_symbol(symbol)
                prices[symbol] = provider.fetch_price(symbol)
            except PriceFailure as failure:
                failures[symbol] = failure
            except Exception as exc:
                logger.error("Unexpected price update error for %s: %s", symbol, exc)
                failures[symbol] = PriceFailure(
                    symbol=symbol,
                    reason=REASON_PRICE_UNAVAILABLE,
                    message=str(exc),
                )

        return PriceUpdateBatch(prices=prices, failures=failures)
