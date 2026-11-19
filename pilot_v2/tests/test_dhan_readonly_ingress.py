"""Offline fail-closed Dhan-only ingress boundary tests, no network."""
import unittest

from pilot_v2.dhan_readonly_ingress import (
    IngressRejected, normalize_dhan_readonly,
)


NOW = 1800000000
INDICES = ("NIFTY", "BANKNIFTY", "SENSEX")


def rows(symbols, observed_at=NOW):
    return {s: {"price": 100.0, "observed_at": observed_at} for s in symbols}


class IngressTests(unittest.TestCase):
    def call(self, selected=("RELIANCE",), rows_arg=None, feed="quotes",
             revision=4, observed_at=NOW):
        return normalize_dhan_readonly(
            feed=feed, selected=selected,
            rows=rows_arg if rows_arg is not None else rows(selected),
            revision=revision, observed_at=observed_at, now=NOW)

    def test_one_equity_unverified_only(self):
        snapshot = self.call()
        self.assertEqual(snapshot["source"], "dhan")
        self.assertEqual(snapshot["freshness"], "unverified")
        self.assertFalse(snapshot["live_orders_enabled"])
        self.assertFalse(snapshot["quotes"]["RELIANCE"]["live_verified"])

    def test_three_indices_independent(self):
        snapshot = self.call(selected=INDICES, feed="indices")
        self.assertEqual(set(snapshot["quotes"]), set(INDICES))

    def test_seventy_cap_and_duplicate_rejected(self):
        with self.assertRaises(IngressRejected):
            self.call(selected=("RELIANCE",) * 2)
        with self.assertRaises(IngressRejected):
            self.call(selected=("RELIANCE",) * 71)

    def test_unhashable_symbol_denied(self):
        with self.assertRaises(IngressRejected):
            self.call(selected=(["RELIANCE"],))

    def test_missing_and_extra_rows_fail_closed(self):
        with self.assertRaises(IngressRejected):
            self.call(rows_arg={})
        with self.assertRaises(IngressRejected):
            self.call(rows_arg={**rows(("RELIANCE",)), **rows(("TCS",))})

    def test_invalid_prices_rejected(self):
        for bad in (0, -2, float("nan"), float("inf"), True, "100"):
            with self.subTest(bad=str(bad)):
                with self.assertRaises(IngressRejected):
                    self.call(rows_arg={"RELIANCE": {
                        "price": bad, "observed_at": NOW}})

    def test_stale_future_and_mixed_timestamp_denied(self):
        for timestamp in (NOW - 8 * 86400, NOW + 6):
            with self.assertRaises(IngressRejected):
                self.call(observed_at=timestamp)
        with self.assertRaises(IngressRejected):
            self.call(rows_arg=rows(("RELIANCE",), NOW - 1))

    def test_no_synthetic_live_claim_or_index_in_equity(self):
        with self.assertRaises(IngressRejected):
            self.call(selected=("NIFTY",))
        with self.assertRaises(IngressRejected):
            self.call(selected=("RELIANCE",), rows_arg={
                "RELIANCE": {"price": 100, "observed_at": NOW,
                             "live_verified": True}})


if __name__ == "__main__":
    unittest.main()
