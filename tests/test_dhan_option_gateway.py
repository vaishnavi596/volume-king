"""Offline contract checks for the Oracle Dhan option gateway."""
import pytest
from unittest.mock import patch
from market_feed import FeedError
from server_feed import ServerDhanReadOnly


def feed():
    client = ServerDhanReadOnly()
    client._origin = "https://example.org"
    client._pairing_key = "test-only"
    return client


def test_expiries_are_broker_listed_and_validated():
    client = feed()
    with patch.object(client, "_call", return_value={
        "source": "dhan", "symbol": "NIFTY", "expiries": ["2026-11-17", "2026-11-23"],
        "live_orders_enabled": False,
    }) as call:
        assert client.option_expiries("NIFTY") == ["2026-11-17", "2026-11-23"]
        call.assert_called_once_with("/dhan/option-expiries", {"symbol": "NIFTY"})
    with pytest.raises(FeedError):
        client.option_expiries("BANKNIFTY")


@pytest.mark.parametrize("dates", [
    [], ["2026-11-23", "2026-11-17"], ["2026-11-17", "2026-11-17"],
    ["2026-11-19", "not-a-date"],
])
def test_invalid_expiry_lists_rejected(dates):
    client = feed()
    with patch.object(client, "_call", return_value={
        "source": "dhan", "symbol": "NIFTY", "expiries": dates,
    }):
        with pytest.raises(FeedError):
            client.option_expiries("NIFTY")


def test_option_metrics_are_read_only_and_unverified():
    client = feed()
    payload = {
        "source": "dhan", "symbol": "NIFTY", "expiry": "2026-11-17",
        "pcr": 0.83049, "max_pain": 25100.0, "freshness": "unverified",
        "signal_eligible": False, "live_orders_enabled": False,
    }
    with patch.object(client, "_call", return_value=payload) as call:
        assert client.option_chain_metrics("NIFTY", "2026-11-17")["pcr"] == 0.83049
        call.assert_called_once_with("/dhan/option-chain", {
            "symbol": "NIFTY", "expiry": "2026-11-17",
        })
    for field, value in [("signal_eligible", True), ("freshness", "exchange_verified"),
                         ("pcr", float("nan")), ("max_pain", None)]:
        with patch.object(client, "_call", return_value={**payload, field: value}):
            with pytest.raises(FeedError):
                client.option_chain_metrics("NIFTY", "2026-11-17")


def test_invalid_option_requests_fail_before_network():
    client = feed()
    with patch.object(client, "_call", side_effect=AssertionError("network called")):
        with pytest.raises(FeedError):
            client.option_chain_metrics("BANKNIFTY", "2026-11-17")
        with pytest.raises(FeedError):
            client.option_chain_metrics("NIFTY", "not-a-date")
