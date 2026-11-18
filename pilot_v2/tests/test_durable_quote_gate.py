"""Offline persistent quote lease tests; no Dhan/API calls."""
import tempfile
import unittest
from pathlib import Path
from pilot_v2.durable_quote_gate import DurableQuoteGate
from pilot_v2.gateway_contract import ContractError,plan_demand

class DurableLeaseTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        path=Path(tmp.name)/"rate.sqlite"
        self.t=[100.]
        self.one=DurableQuoteGate(path,clock=lambda:self.t[0])
        self.two=DurableQuoteGate(path,clock=lambda:self.t[0])

    def demand(self,syms):
        return plan_demand([syms,[],[],[],[]])

    def test_two_workers_share_one_lease_and_attempt_clock(self):
        d=self.demand(["TCS"])
        lease=self.one.begin(d)
        self.assertEqual(len(lease.symbols),4)
        self.assertIsNone(self.two.begin(d))
        self.two.complete(lease)
        self.t[0]+=1
        self.assertIsNone(self.two.begin(d))
        self.t[0]+=59
        next_lease=self.two.begin(d)
        self.assertEqual(next_lease.symbols,lease.symbols)
        self.one.complete(next_lease)

    def test_new_equity_and_zero_equity_indices(self):
        first=self.one.begin(self.demand(["TCS"]))
        self.one.complete(first)
        self.t[0]+=1
        second=self.two.begin(self.demand(["TCS","INFY"]))
        self.assertEqual(second.symbols,("INFY",))
        self.two.complete(second)
        self.t[0]+=60
        self.assertEqual(len(self.one.begin(self.demand([])).symbols),3)

    def test_429_persists_restart_and_invalid_retry_denied(self):
        d=self.demand(["TCS"])
        lease=self.one.begin(d)
        with self.assertRaises(ContractError):
            self.one.complete(lease,retry_after=0)
        self.one.complete(lease,retry_after=90)
        self.t[0]+=60
        self.assertIsNone(self.two.begin(d))
        self.assertEqual(self.two.state()["cooldown_seconds"],30)
        self.t[0]+=30
        self.assertIsNotNone(self.two.begin(d))

    def test_crash_lease_timeout_and_stale_completion(self):
        old=self.one.begin(self.demand(["TCS"]))
        self.t[0]+=30
        fresh=self.two.begin(self.demand(["TCS","INFY"]))
        self.assertEqual(fresh.symbols,("INFY",))
        with self.assertRaises(ContractError):
            self.one.complete(old)
        self.two.complete(fresh)

    def test_clock_regression_fails_closed(self):
        d=self.demand(["TCS"])
        first=self.one.begin(d);self.one.complete(first)
        self.t[0]=50
        self.assertIsNone(self.two.begin(d))

    def test_seventy_equities_three_indexes_and_validation(self):
        lease=self.one.begin(self.demand([f"EQ{i:03d}" for i in range(70)]))
        self.assertEqual(len(lease.symbols),73)
        self.one.complete(lease)
        with self.assertRaises(ValueError):
            DurableQuoteGate(self.one.path,clock=lambda:0,global_spacing=0)

if __name__=="__main__":
    unittest.main()
