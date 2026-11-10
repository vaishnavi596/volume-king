"""Offline tests for independent provider status and stale-data fallback."""
import unittest
from backend.provider_router import ProviderState, choose_source


class ProviderRouterTests(unittest.TestCase):
    def test_prefers_fresh_dhan(self):
        states = [ProviderState("Dhan", "CONNECTED", 99)]
        self.assertEqual(choose_source(states, now=100)["provider"], "Dhan")

    def test_expired_dhan_has_no_fallback(self):
        states = [ProviderState("Dhan", "EXPIRED", 99)]
        result = choose_source(states, now=100)
        self.assertIsNone(result["provider"])
        self.assertFalse(result["fallback"])

    def test_legacy_provider_rejected(self):
        for name in ("Yahoo Finance", "Angel One"):
            with self.assertRaises(ValueError):
                ProviderState(name, "CONNECTED", 99)

    def test_stale_and_future_data_are_not_live(self):
        for timestamp in (1, 101):
            states = [ProviderState("Dhan", "CONNECTED", timestamp)]
            self.assertEqual(choose_source(states, now=100, max_age_seconds=10)["status"], "UNAVAILABLE")

    def test_unconfigured_provider_cannot_be_selected(self):
        states = [ProviderState("Dhan", "NOT_CONFIGURED", 99)]
        self.assertIsNone(choose_source(states, now=100)["provider"])

    def test_invalid_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            ProviderState("Unknown", "CONNECTED")


if __name__ == "__main__":
    unittest.main()
