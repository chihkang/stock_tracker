from stock_tracker.providers.market_data import (
    MarketDataService,
    YahooFinanceProvider,
    YahooTaiwanProvider,
)


def test_taiwan_provider_normalizes_tpe_symbols_for_yahoo_taiwan():
    provider = YahooTaiwanProvider()

    assert provider.supports("006208:TPE")
    assert provider.normalize_symbol("006208:TPE") == "006208.TW"
    assert provider.normalize_symbol("2330:TPE") == "2330.TW"


def test_us_provider_normalizes_us_symbols_for_yahoo_finance():
    provider = YahooFinanceProvider()

    assert provider.supports("AAPL:NASDAQ")
    assert provider.supports("VTI:NYSEARCA")
    assert provider.normalize_symbol("AAPL:NASDAQ") == "AAPL"
    assert provider.normalize_symbol("VTI:NYSEARCA") == "VTI"


def test_market_data_service_routes_by_symbol_exchange_suffix():
    service = MarketDataService(
        providers=[
            YahooTaiwanProvider(),
            YahooFinanceProvider(),
        ]
    )

    assert isinstance(service.provider_for_symbol("006208:TPE"), YahooTaiwanProvider)
    assert isinstance(service.provider_for_symbol("AAPL:NASDAQ"), YahooFinanceProvider)
    assert isinstance(service.provider_for_symbol("VTI:NYSEARCA"), YahooFinanceProvider)


def test_us_provider_prefers_quote_price_over_unrelated_market_streamers():
    provider = YahooFinanceProvider()
    html = """
    <fin-streamer data-symbol="ES=F" data-field="regularMarketPrice">7,261.75</fin-streamer>
    <section data-testid="quote-price">
      <span data-testid="qsp-price">280.25 </span>
    </section>
    """

    assert provider._parse_price(html, "AAPL") == 280.25
