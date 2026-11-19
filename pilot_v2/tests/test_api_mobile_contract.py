"""Shared versioned mock server + mock mobile contract tests, no network."""
import unittest
from pilot_v2.api_contract import (API_PREFIX,ENABLED_BY_DEFAULT,
                                    make_snapshot,parse_selection,validate_snapshot)
from pilot_v2.mobile_contract_mock import V2MobileFixture
from pilot_v2.gateway_contract import ContractError

def q(value,rev):
    return {"price":value,"freshness":"unverified","live_verified":False,"revision":rev}

class ContractTests(unittest.TestCase):
    def test_api_disabled_and_separate(self):
        self.assertEqual(API_PREFIX,"/v2-pilot")
        self.assertIs(ENABLED_BY_DEFAULT,False)

    def test_zero_five_fifty_one_seventy(self):
        for n in (0,5,51,70):
            with self.subTest(n=n):
                m=V2MobileFixture()
                self.assertEqual(m.select({"watchlists":[[f"EQ{i:03d}" for i in range(n)],[],[],[],[]]}),n)

    def test_last_good_and_indices(self):
        m=V2MobileFixture()
        m.select({"watchlists":[["TCS","INFY"],[],[],[],[]]})
        m.apply(make_snapshot(1,{"TCS":q(100,1),"INFY":q(200,1),"NIFTY":q(25000,1)}))
        m.apply(make_snapshot(2,{"TCS":q(110,2)}))
        self.assertFalse(m.apply(make_snapshot(1,{"TCS":q(10,1)})))
        self.assertEqual(m.quotes["INFY"]["price"],200)
        self.assertEqual(m.quotes["NIFTY"]["price"],25000)
        self.assertEqual(m.quotes["TCS"]["price"],110)

    def test_newer_envelope_cannot_relabel_older_symbol_data(self):
        m = V2MobileFixture()
        m.select({"watchlists": [["TCS", "INFY"], [], [], [], []]})
        self.assertTrue(m.apply(make_snapshot(10, {
            "TCS": q(120, 10), "INFY": q(200, 8)})))
        self.assertTrue(m.apply(make_snapshot(11, {
            "TCS": q(99, 9), "INFY": q(205, 11)})))
        self.assertEqual(m.quotes["TCS"]["price"], 120)
        self.assertEqual(m.quotes["TCS"]["revision"], 10)
        self.assertEqual(m.quotes["INFY"]["price"], 205)
        self.assertTrue(m.apply(make_snapshot(12, {
            "TCS": q(75, 10), "INFY": q(1, 11)})))
        self.assertEqual(m.quotes["TCS"]["price"], 120)
        self.assertEqual(m.quotes["INFY"]["price"], 205)
        self.assertEqual(m.revision, 12)
        self.assertFalse(m.apply(make_snapshot(12, {"TCS": q(150, 12)})))

    def test_never_trust_live_token_orders_or_unselected(self):
        m=V2MobileFixture()
        m.select({"watchlists":[["TCS"],[],[],[],[]]})
        good=make_snapshot(1,{"TCS":q(100,1)})
        for p in (dict(good,live_orders_enabled=True),
                  dict(good,source="yahoo"),
                  dict(good,schema_version=2),
                  dict(good,access_token="secret"),
                  make_snapshot(2,{"INFY":q(200,2)})):
            with self.assertRaises(ContractError):
                m.apply(p)

    def test_gateway_and_mobile_reject_boolean_schema_version(self):
        baseline = make_snapshot(7, {"TCS": q(100, 7)})
        for invalid in (dict(baseline, schema_version=True),
                        dict(baseline, schema_version=1.0),
                        dict(baseline, schema_version=False)):
            with self.subTest(schema=invalid["schema_version"]):
                with self.assertRaises(ContractError):
                    validate_snapshot(invalid)
                m = V2MobileFixture()
                m.select({"watchlists": [["TCS"], [], [], [], []]})
                with self.assertRaises(ContractError):
                    m.apply(invalid)
                self.assertEqual(m.quotes, {})

    def test_gateway_rejects_noncanonical_quote_symbols_before_delivery(self):
        for name in ("", "tcs", " TCS", "TCS ", "TCS/NSE",
                     "A" * 33, "TCS\\nBAD", "NIFTY!"):
            with self.subTest(name=repr(name)), self.assertRaises(ContractError):
                make_snapshot(5, {name: q(101, 5)})
        self.assertEqual(make_snapshot(5, {"NIFTY": q(25000, 5)})
                         ["quotes"]["NIFTY"]["price"], 25000)
        self.assertEqual(make_snapshot(5, {"TCS": q(101, 5)})
                         ["quotes"]["TCS"]["price"], 101)

    def test_invalid_selection_and_prices(self):
        for body in ({"watchlists":[["TCS"],["TCS"],[],[],[]]},
                     {"watchlists":[[f"EQ{i:03d}" for i in range(71)],[],[],[],[]]},
                     {"watchlists":[]},{"watchlists":[[],[],[],[],[]],"master":True}):
            with self.assertRaises(ContractError):
                parse_selection(body)
        with self.assertRaises(ContractError):
            make_snapshot(1,{"TCS":q(-1,1)})
        with self.assertRaises(ContractError):
            make_snapshot(1,{"TCS":dict(q(100,1),live_verified=True)})

if __name__=="__main__":
    unittest.main()
