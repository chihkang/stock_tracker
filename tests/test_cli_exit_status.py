import asyncio
import sys
from types import SimpleNamespace

import stock_tracker.__main__ as cli


class FakePortfolioManager:
    def __init__(self, status):
        self.status = status

    async def initialize(self):
        return self

    async def update_prices(self):
        return SimpleNamespace(status=self.status)

    def print_portfolio(self):
        return None


def run_cli_with_status(monkeypatch, status):
    manager = FakePortfolioManager(status)
    monkeypatch.setenv("GIST_ID", "gist-id")
    monkeypatch.setenv("GIST_TOKEN", "gist-token")
    monkeypatch.setattr(cli, "GistManager", lambda *args, **kwargs: object())
    monkeypatch.setattr(cli, "PortfolioManager", lambda *args, **kwargs: manager)
    monkeypatch.setattr(sys, "argv", ["stock_tracker", "portfolio", "-f"])

    return asyncio.run(cli.async_main())


def test_cli_returns_zero_for_success(monkeypatch):
    assert run_cli_with_status(monkeypatch, "success") == 0


def test_cli_returns_non_zero_for_partial_success(monkeypatch):
    assert run_cli_with_status(monkeypatch, "partial_success") == 1


def test_cli_returns_non_zero_for_failed(monkeypatch):
    assert run_cli_with_status(monkeypatch, "failed") == 1
