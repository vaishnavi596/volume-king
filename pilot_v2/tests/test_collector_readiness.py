"""Pure Dhan capability evidence and split-provider plan tests. No network."""
import unittest
from pilot_v2.collector_readiness import (ProviderCapabilities,
                                            plan_collector,EQUITY_ROUTE,INDEX_ROUTE)
from pilot_v2.broker_token_status import classify_dhan_token
from pilot_v2.gateway_contract import plan_demand,ContractError

def cap(**overrides):
    fields=dict(observed_on_oracle=False,authenticated=False,quote_equities=False,
                quote_indices=False,historical_candles=False,option_chain=False,
                renewal_supported=False)
    fields.update(overrides)
    return ProviderCapabilities(**fields)

def token(renew=False,expires=5000):
    return classify_dhan_token(now=1000,expires_at=expires,
                               renewal_supported=renew,configured=True)

class ProviderReadinessTests(unittest.TestCase):
    def test_no_oracle_observation_disallows_even_optimistic_flags(self):
        c=cap(authenticated=True,quote_equities=True,quote_indices=True)
        plan=plan_collector(plan_demand([["TCS"],[],[],[],[]]),c,token())
        self.assertFalse(plan.ready)
        self.assertEqual(plan.reason,"ORACLE_RUNTIME_UNVERIFIED")
        self.assertEqual(plan.lanes,())

    def test_split_index_and_equity_even_for_70(self):
        c=cap(observed_on_oracle=True,authenticated=True,
              quote_equities=True,quote_indices=True)
        for n in (0,5,51,70):
            with self.subTest(n=n):
                equities=[f"EQ{i:03d}" for i in range(n)]
                plan=plan_collector(plan_demand([equities,[],[],[],[]]),c,token())
                self.assertTrue(plan.ready)
                self.assertEqual(len(plan.lanes),2 if n else 1)
                self.assertEqual(plan.lanes[-1].route,INDEX_ROUTE)
                if n:
                    self.assertEqual(plan.lanes[0].route,EQUITY_ROUTE)
                    self.assertEqual(len(plan.lanes[0].symbols),n)
                self.assertTrue(plan.unverified)

    def test_unknown_broker_entitlements_fail_closed(self):
        d=plan_demand([["TCS"],[],[],[],[]])
        base=cap(observed_on_oracle=True,authenticated=True,quote_indices=True)
        self.assertEqual(plan_collector(d,base,token()).reason,
                         "EQUITY_QUOTES_UNAVAILABLE")
        index_only=plan_collector(plan_demand([[],[],[],[],[]]),base,token())
        self.assertTrue(index_only.ready)
        bad=cap(observed_on_oracle=True,authenticated=True,quote_equities=True)
        self.assertEqual(plan_collector(d,bad,token()).reason,"INDEX_QUOTES_UNAVAILABLE")

    def test_expired_token_stops_all_and_nonrenewable_warns(self):
        c=cap(observed_on_oracle=True,authenticated=True,
              quote_equities=True,quote_indices=True)
        d=plan_demand([["TCS"],[],[],[],[]])
        self.assertEqual(plan_collector(d,c,token(expires=1000)).reason,
                         "BROKER_AUTH_UNAVAILABLE")
        soon=classify_dhan_token(now=1000,expires_at=1100,
                                 configured=True,renewal_supported=False)
        self.assertEqual(soon.state,"REAUTH_SOON")
        self.assertTrue(soon.needs_user_reauth)

    def test_bad_capability_types_are_not_assumed_true(self):
        with self.assertRaises(ContractError):
            cap(observed_on_oracle="true")
        with self.assertRaises(ContractError):
            plan_collector(None,cap(),token())

if __name__=="__main__":
    unittest.main()
