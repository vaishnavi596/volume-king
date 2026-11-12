"""Offline tests for independent provider status and stale-data fallback."""
import unittest
from backend.provider_router import ProviderState, choose_source


class ProviderRouterTests(unittest.TestCase):
    def test_prefers_fresh_dhan(self):
        states = [ProviderState("Yahoo Finance", "CONNECTED", 90),
                  ProviderState("Dhan", "CONNECTED", 99)]
        self.assertEqual(choose_source(states, now=100)["provider"], "Dhan")

    def test_yahoo_fallback_is_explicit(self):
        states = [ProviderState("Dhan", "EXPIRED", 99),
                  ProviderState("Yahoo Finance", "CONNECTED", 95)]
        result = choose_source(states, now=100, allow_fallback=True)
        self.assertEqual(result["provider"], "Yahoo Finance")
        self.assertTrue(result["fallback"])

    def test_dhan_failure_does_not_silently_switch_to_yahoo(self):
        states = [ProviderState("Dhan", "EXPIRED", 99),
                  ProviderState("Yahoo Finance", "CONNECTED", 95)]
        result = choose_source(states, now=100)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIsNone(result["provider"])

    def test_angel_one_remains_optional(self):
        states = [ProviderState("Angel One", "CONNECTED", 99)]
        self.assertEqual(choose_source(states, preferred="Angel One", now=100)["provider"], "Angel One")

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
