"""Shared versioned mock server + mock mobile contract tests, no network."""
import unittest
from pilot_v2.api_contract import (API_PREFIX,ENABLED_BY_DEFAULT,
                                    make_snapshot,parse_selection)
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
