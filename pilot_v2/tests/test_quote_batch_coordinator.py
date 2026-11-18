"""No-network rate-budget tests for one shared 1–3 device Dhan quote plan."""
import unittest
from pilot_v2.quote_batch_coordinator import QuoteBatchCoordinator
from pilot_v2.gateway_contract import ContractError, plan_demand

class QuoteCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.now=[100.]
        self.coord=QuoteBatchCoordinator(clock=lambda:self.now[0],
                                         minimum_spacing=1,per_symbol_interval=60)

    def test_zero_selected_equities_still_has_separate_three_indices(self):
        d=plan_demand([[],[],[],[],[]])
        lease=self.coord.next_batch(d)
        self.assertEqual(set(lease.symbols),{"NIFTY","BANKNIFTY","SENSEX"})
        self.coord.finish(lease)
        self.assertIsNone(self.coord.next_batch(d))

    def test_same_union_demand_three_phones_only_one_lease(self):
        d=plan_demand([["TCS","RELIANCE"],[],[],[],[]])
        first=self.coord.next_batch(d)
        self.assertEqual(len(first.symbols),5)
        self.assertIsNone(self.coord.next_batch(d))
        self.coord.finish(first)
        self.now[0]+=1
        self.assertIsNone(self.coord.next_batch(d))
        self.now[0]+=59
        second=self.coord.next_batch(d)
        self.assertEqual(set(second.symbols),set(first.symbols))
        self.coord.finish(second)

    def test_new_share_can_join_when_global_gap_allows_but_cached_share_not_refetched(self):
        d1=plan_demand([["TCS"],[],[],[],[]])
        d2=plan_demand([["TCS","INFY"],[],[],[],[]])
        first=self.coord.next_batch(d1)
        self.coord.finish(first)
        self.now[0]+=.5
        self.assertIsNone(self.coord.next_batch(d2))
        self.now[0]+=.5
        second=self.coord.next_batch(d2)
        self.assertEqual(second.symbols,("INFY",))
        self.coord.finish(second)

    def test_429_cooldown_no_repeat_even_when_other_device_requests(self):
        d=plan_demand([["TCS"],[],[],[],[]])
        lease=self.coord.next_batch(d)
        self.coord.cooldown_429(lease,retry_after_seconds=90)
        self.now[0]+=60
        self.assertIsNone(self.coord.next_batch(d))
        self.assertEqual(self.coord.state()["cooldown_seconds"],30)
        self.now[0]+=30
        again=self.coord.next_batch(d)
        self.assertIsNotNone(again)
        self.coord.finish(again)

    def test_invalid_lease_no_bypass_and_retry_floor(self):
        d=plan_demand([["TCS"],[],[],[],[]])
        lease=self.coord.next_batch(d)
        with self.assertRaises(ContractError):
            self.coord.finish(None)
        with self.assertRaises(ContractError):
            self.coord.cooldown_429(None)
        with self.assertRaises(ContractError):
            self.coord.cooldown_429(lease,retry_after_seconds=0)
        self.assertTrue(self.coord.state()["pending"])
        self.coord.finish(lease)
        with self.assertRaises(ContractError):
            self.coord.finish(lease)

    def test_bounded_seventy_plus_three_and_invalid_configs(self):
        symbols=[f"EQ{i:03d}" for i in range(70)]
        lease=self.coord.next_batch(plan_demand([symbols,[],[],[],[]]))
        self.assertEqual(len(lease.symbols),73)
        self.coord.finish(lease)
        for opts in ({"minimum_spacing":0},{"per_symbol_interval":0},
                     {"max_symbols":74},{"minimum_spacing":float("nan")}):
            with self.subTest(opts=opts),self.assertRaises(ValueError):
                QuoteBatchCoordinator(clock=lambda:100,**opts)

    def test_failure_close_does_not_create_immediate_second_request(self):
        d=plan_demand([["TCS"],[],[],[],[]])
        lease=self.coord.next_batch(d)
        self.coord.finish(lease)
        self.now[0]+=.1
        self.assertIsNone(self.coord.next_batch(d))

if __name__=="__main__":
    unittest.main()
