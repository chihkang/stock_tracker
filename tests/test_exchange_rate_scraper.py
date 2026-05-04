from unittest.mock import MagicMock, patch

from stock_tracker.scraper.exchange_rate_scraper import get_exchange_rate


def test_get_exchange_rate_reads_twd_from_public_json_endpoint():
    response = MagicMock()
    response.json.return_value = {
        "result": "success",
        "base_code": "USD",
        "rates": {
            "TWD": 31.653294,
        },
    }

    with patch("requests.get", return_value=response):
        assert get_exchange_rate("USD-TWD") == 31.65
