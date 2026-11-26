import unittest

from v3_oi_filter_votes import oi_filter_vote


def chain(ce, pe, max_pain=25200.0, strikes=(24900, 25000, 25100, 25200, 25300, 25400, 25500)):
    rows = [{"strike": float(k), "ce": {"oi": float(c)}, "pe": {"oi": float(p)}}
            for k, c, p in zip(strikes, ce, pe)]
    return {"source": "dhan", "symbol": "NIFTY", "expiry": "2026-12-01",
            "freshness": "unverified", "signal_eligible": False, "pcr": 1.0,
            "max_pain": max_pain,
            "atm_window": {"source": "dhan", "atm": 25200.0, "rows": rows,
                           "freshness": "unverified", "signal_eligible": False}}


FLAT = (100, 100, 100, 100, 100, 100, 100)


class OiFilterVoteTests(unittest.TestCase):
    def test_support_held_breached_and_untested(self):
        put_wall = (100, 900, 100, 100, 100, 100, 100)  # wall at 25000
        data = chain(FLAT, put_wall)
        self.assertEqual(oi_filter_vote("OI Support", data, 25050.0)[0], 1)   # within 0.5%
        self.assertEqual(oi_filter_vote("OI Support", data, 25400.0)[0], 0)   # not tested
        self.assertEqual(oi_filter_vote("OI Support", data, 24950.0)[0], -1)  # breached

    def test_resistance_broken_capped_and_untested(self):
        call_wall = (100, 100, 100, 100, 100, 900, 100)  # wall at 25400
        data = chain(call_wall, FLAT)
        self.assertEqual(oi_filter_vote("OI Resistance", data, 25450.0)[0], 1)
        self.assertEqual(oi_filter_vote("OI Resistance", data, 25350.0)[0], -1)
        self.assertEqual(oi_filter_vote("OI Resistance", data, 25000.0)[0], 0)

    def test_profile_ratio(self):
        self.assertEqual(oi_filter_vote("OI Profile", chain(FLAT, (200,) * 7), 25200.0)[0], 1)
        self.assertEqual(oi_filter_vote("OI Profile", chain((200,) * 7, FLAT), 25200.0)[0], -1)
        self.assertEqual(oi_filter_vote("OI Profile", chain(FLAT, FLAT), 25200.0)[0], 0)

    def test_max_pain_pull(self):
        self.assertEqual(oi_filter_vote("Dhan Max Pain", chain(FLAT, FLAT, 25300.0), 25200.0)[0], 1)
        self.assertEqual(oi_filter_vote("Dhan Max Pain", chain(FLAT, FLAT, 25100.0), 25200.0)[0], -1)
        self.assertEqual(oi_filter_vote("Dhan Max Pain", chain(FLAT, FLAT, 25205.0), 25200.0)[0], 0)

    def test_fail_closed(self):
        data = chain(FLAT, FLAT)
        for name in ("OI Support", "OI Resistance", "OI Profile", "Dhan Max Pain"):
            for spot in (None, 0, -1, float("nan"), True, "25200"):
                self.assertIsNone(oi_filter_vote(name, data, spot)[0])
            self.assertIsNone(oi_filter_vote(name, {}, 25200.0)[0])
            self.assertIsNone(oi_filter_vote(name, dict(data, source="yahoo"), 25200.0)[0])
        self.assertIsNone(oi_filter_vote("OI Support", chain(FLAT, (0,) * 7), 25200.0)[0])
        self.assertIsNone(oi_filter_vote("Dhan Max Pain", chain(FLAT, FLAT, None), 25200.0)[0])
        self.assertIsNone(oi_filter_vote("RSI", data, 25200.0)[0])


if __name__ == "__main__":
    unittest.main()
