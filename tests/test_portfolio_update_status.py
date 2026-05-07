import asyncio
import json
from copy import deepcopy

from stock_tracker.portfolio.portfolio_manager import PortfolioManager
from stock_tracker.providers.market_data import (
    ExchangeRateFailure,
    PriceFailure,
    PriceResult,
    PriceUpdateBatch,
)


class FakeGistManager:
    def __init__(self, portfolio, history=None):
        self.portfolio = deepcopy(portfolio)
        self.history = deepcopy(history) if history is not None else {"values": []}
        self.saved_portfolios = []
        self.saved_histories = []

    async def read_portfolio(self):
        return deepcopy(self.portfolio)

    async def read_history(self):
        return deepcopy(self.history)

    async def update_portfolio(self, portfolio_data, history_data=None):
        self.saved_portfolios.append(deepcopy(portfolio_data))
        if history_data is not None:
            self.saved_histories.append(deepcopy(history_data))
        return True

    async def create_backup(self, portfolio_data, backup_dir="backups"):
        return True


class FakePriceService:
    def __init__(self, batch):
        self.batch = batch

    async def get_prices(self, symbols):
        self.requested_symbols = list(symbols)
        return self.batch


class FakeExchangeRateService:
    def __init__(self, result):
        self.result = result

    async def get_rate(self, currency_pair="USD-TWD"):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def base_portfolio():
    return {
        "totalValue": 1000.0,
        "exchange rate": "31.54",
        "exchange_rate_updated": "2026-04-28T22:23:00+08:00",
        "stocks": [
            {
                "name": "2330:TPE",
                "price": 100.0,
                "quantity": 3,
                "currency": "TWD",
                "lastUpdated": "2026-04-28T14:21:53+08:00",
                "percentageOfTotal": 30.0,
            },
            {
                "name": "AAPL:NASDAQ",
                "price": 10.0,
                "quantity": 2,
                "currency": "USD",
                "lastUpdated": "2026-04-28T23:57:31+08:00",
                "percentageOfTotal": 70.0,
            },
        ],
    }


def test_full_success_updates_prices_status_and_returns_success(tmp_path):
    asyncio.run(_assert_full_success_updates_prices_status_and_returns_success(tmp_path))


async def _assert_full_success_updates_prices_status_and_returns_success(tmp_path):
    portfolio = base_portfolio()
    gist = FakeGistManager(portfolio)
    batch = PriceUpdateBatch(
        prices={
            "2330:TPE": PriceResult(
                symbol="2330:TPE",
                price=120.0,
                currency="TWD",
                retrieved_at="2026-05-04T15:00:00+08:00",
                source="test",
            ),
            "AAPL:NASDAQ": PriceResult(
                symbol="AAPL:NASDAQ",
                price=12.0,
                currency="USD",
                retrieved_at="2026-05-04T15:00:01+08:00",
                source="test",
            ),
        },
        failures={},
    )
    manager = PortfolioManager(
        file_path=str(tmp_path / "portfolio.json"),
        gist_manager=gist,
        force_update=True,
        price_service=FakePriceService(batch),
        exchange_rate_service=FakeExchangeRateService(32.0),
    )

    await manager.initialize()
    result = await manager.update_prices()

    assert result.status == "success"
    saved = gist.saved_portfolios[-1]
    assert saved["stocks"][0]["price"] == 120.0
    assert saved["stocks"][1]["price"] == 12.0
    assert saved["exchange rate"] == "32.00"
    assert saved["updateStatus"]["status"] == "success"
    assert saved["updateStatus"]["updatedSymbols"] == ["2330:TPE", "AAPL:NASDAQ"]
    assert saved["updateStatus"]["failedSymbols"] == []
    history = gist.saved_histories[-1]
    assert history["updatedAt"] == saved["updateStatus"]["retrieved_at"]
    assert history["values"][-1] == {
        "date": saved["updateStatus"]["retrieved_at"][:10],
        "totalValueTwd": 1128.0,
        "sourceUpdatedAt": saved["updateStatus"]["retrieved_at"],
    }
    with open(tmp_path / "portfolio-history.json", encoding="utf-8") as f:
        local_history = json.load(f)
    assert local_history == history


def test_partial_success_writes_successful_prices_and_marks_partial(tmp_path):
    asyncio.run(_assert_partial_success_writes_successful_prices_and_marks_partial(tmp_path))


async def _assert_partial_success_writes_successful_prices_and_marks_partial(tmp_path):
    portfolio = base_portfolio()
    gist = FakeGistManager(portfolio)
    batch = PriceUpdateBatch(
        prices={
            "2330:TPE": PriceResult(
                symbol="2330:TPE",
                price=120.0,
                currency="TWD",
                retrieved_at="2026-05-04T15:00:00+08:00",
                source="test",
            )
        },
        failures={
            "AAPL:NASDAQ": PriceFailure(
                symbol="AAPL:NASDAQ",
                reason="price_unavailable",
                message="No provider returned a valid price",
            )
        },
    )
    manager = PortfolioManager(
        file_path=str(tmp_path / "portfolio.json"),
        gist_manager=gist,
        force_update=True,
        price_service=FakePriceService(batch),
        exchange_rate_service=FakeExchangeRateService(31.54),
    )

    await manager.initialize()
    result = await manager.update_prices()

    assert result.status == "partial_success"
    saved = gist.saved_portfolios[-1]
    assert saved["stocks"][0]["price"] == 120.0
    assert saved["stocks"][1]["price"] == 10.0
    assert saved["updateStatus"]["status"] == "partial_success"
    assert saved["updateStatus"]["updatedSymbols"] == ["2330:TPE"]
    assert saved["updateStatus"]["failedSymbols"] == [
        {
            "symbol": "AAPL:NASDAQ",
            "reason": "price_unavailable",
            "message": "No provider returned a valid price",
        }
    ]
    assert gist.saved_histories == []
    assert not (tmp_path / "portfolio-history.json").exists()


def test_failed_update_only_writes_update_status(tmp_path):
    asyncio.run(_assert_failed_update_only_writes_update_status(tmp_path))


async def _assert_failed_update_only_writes_update_status(tmp_path):
    portfolio = base_portfolio()
    gist = FakeGistManager(portfolio)
    batch = PriceUpdateBatch(
        prices={},
        failures={
            "2330:TPE": PriceFailure(symbol="2330:TPE", reason="price_unavailable"),
            "AAPL:NASDAQ": PriceFailure(symbol="AAPL:NASDAQ", reason="price_unavailable"),
        },
    )
    manager = PortfolioManager(
        file_path=str(tmp_path / "portfolio.json"),
        gist_manager=gist,
        force_update=True,
        price_service=FakePriceService(batch),
        exchange_rate_service=FakeExchangeRateService(31.8),
    )

    await manager.initialize()
    result = await manager.update_prices()

    assert result.status == "failed"
    saved = gist.saved_portfolios[-1]
    assert saved["totalValue"] == portfolio["totalValue"]
    assert saved["exchange rate"] == portfolio["exchange rate"]
    assert saved["exchange_rate_updated"] == portfolio["exchange_rate_updated"]
    assert saved["stocks"] == portfolio["stocks"]
    assert saved["updateStatus"]["status"] == "failed"
    assert saved["updateStatus"]["updatedSymbols"] == []
    assert gist.saved_histories == []
    assert not (tmp_path / "portfolio-history.json").exists()


def test_exchange_rate_failure_keeps_previous_rate_and_writes_warning(tmp_path):
    asyncio.run(_assert_exchange_rate_failure_keeps_previous_rate_and_writes_warning(tmp_path))


async def _assert_exchange_rate_failure_keeps_previous_rate_and_writes_warning(tmp_path):
    portfolio = base_portfolio()
    gist = FakeGistManager(portfolio)
    batch = PriceUpdateBatch(
        prices={
            "2330:TPE": PriceResult(
                symbol="2330:TPE",
                price=120.0,
                currency="TWD",
                retrieved_at="2026-05-04T15:00:00+08:00",
                source="test",
            ),
            "AAPL:NASDAQ": PriceResult(
                symbol="AAPL:NASDAQ",
                price=12.0,
                currency="USD",
                retrieved_at="2026-05-04T15:00:01+08:00",
                source="test",
            ),
        },
        failures={},
    )
    manager = PortfolioManager(
        file_path=str(tmp_path / "portfolio.json"),
        gist_manager=gist,
        force_update=True,
        price_service=FakePriceService(batch),
        exchange_rate_service=FakeExchangeRateService(
            ExchangeRateFailure(reason="rate_unavailable", message="provider failed")
        ),
    )

    await manager.initialize()
    result = await manager.update_prices()

    assert result.status == "success"
    saved = gist.saved_portfolios[-1]
    assert saved["exchange rate"] == portfolio["exchange rate"]
    assert saved["exchange_rate_updated"] == portfolio["exchange_rate_updated"]
    assert saved["updateStatus"]["exchangeRate"]["status"] == "failed"
    assert saved["updateStatus"]["exchangeRate"]["usedPreviousRate"] is True
    assert "使用舊匯率" in saved["updateStatus"]["exchangeRate"]["message"]
    assert gist.saved_histories[-1]["values"][-1]["totalValueTwd"] == 1116.96


def test_full_success_replaces_existing_history_entry_for_same_day(tmp_path, monkeypatch):
    asyncio.run(_assert_full_success_replaces_existing_history_entry_for_same_day(tmp_path, monkeypatch))


async def _assert_full_success_replaces_existing_history_entry_for_same_day(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "stock_tracker.portfolio.portfolio_manager.get_current_timestamp",
        lambda: "2026-05-07T14:26:19+08:00",
    )
    portfolio = base_portfolio()
    gist = FakeGistManager(
        portfolio,
        history={
            "updatedAt": "2026-05-07T08:00:00+08:00",
            "values": [
                {
                    "date": "2026-05-06",
                    "totalValueTwd": 990.0,
                    "sourceUpdatedAt": "2026-05-06T14:00:00+08:00",
                },
                {
                    "date": "2026-05-07",
                    "totalValueTwd": 1000.0,
                    "sourceUpdatedAt": "2026-05-07T08:00:00+08:00",
                },
            ],
        },
    )
    batch = PriceUpdateBatch(
        prices={
            "2330:TPE": PriceResult(
                symbol="2330:TPE",
                price=120.0,
                currency="TWD",
                retrieved_at="2026-05-07T14:26:00+08:00",
                source="test",
            ),
            "AAPL:NASDAQ": PriceResult(
                symbol="AAPL:NASDAQ",
                price=12.0,
                currency="USD",
                retrieved_at="2026-05-07T14:26:01+08:00",
                source="test",
            ),
        },
        failures={},
    )
    manager = PortfolioManager(
        file_path=str(tmp_path / "portfolio.json"),
        gist_manager=gist,
        force_update=True,
        price_service=FakePriceService(batch),
        exchange_rate_service=FakeExchangeRateService(32.0),
    )

    await manager.initialize()
    result = await manager.update_prices()

    assert result.status == "success"
    history = gist.saved_histories[-1]
    assert history["updatedAt"] == "2026-05-07T14:26:19+08:00"
    assert [entry["date"] for entry in history["values"]] == ["2026-05-06", "2026-05-07"]
    assert history["values"][1] == {
        "date": "2026-05-07",
        "totalValueTwd": 1128.0,
        "sourceUpdatedAt": "2026-05-07T14:26:19+08:00",
    }


def test_full_success_uses_local_seed_when_gist_history_is_missing(tmp_path, monkeypatch):
    asyncio.run(_assert_full_success_uses_local_seed_when_gist_history_is_missing(tmp_path, monkeypatch))


async def _assert_full_success_uses_local_seed_when_gist_history_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "stock_tracker.portfolio.portfolio_manager.get_current_timestamp",
        lambda: "2026-05-07T14:26:19+08:00",
    )
    with open(tmp_path / "portfolio-history.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "updatedAt": "2026-05-06T22:59:23+08:00",
                "values": [
                    {
                        "date": "2026-05-06",
                        "totalValueTwd": 990.0,
                        "sourceUpdatedAt": "2026-05-06T22:59:23+08:00",
                    }
                ],
            },
            f,
        )

    portfolio = base_portfolio()
    gist = FakeGistManager(portfolio, history={"values": []})
    batch = PriceUpdateBatch(
        prices={
            "2330:TPE": PriceResult(
                symbol="2330:TPE",
                price=120.0,
                currency="TWD",
                retrieved_at="2026-05-07T14:26:00+08:00",
                source="test",
            ),
            "AAPL:NASDAQ": PriceResult(
                symbol="AAPL:NASDAQ",
                price=12.0,
                currency="USD",
                retrieved_at="2026-05-07T14:26:01+08:00",
                source="test",
            ),
        },
        failures={},
    )
    manager = PortfolioManager(
        file_path=str(tmp_path / "portfolio.json"),
        gist_manager=gist,
        force_update=True,
        price_service=FakePriceService(batch),
        exchange_rate_service=FakeExchangeRateService(32.0),
    )

    await manager.initialize()
    result = await manager.update_prices()

    assert result.status == "success"
    history = gist.saved_histories[-1]
    assert [entry["date"] for entry in history["values"]] == ["2026-05-06", "2026-05-07"]
