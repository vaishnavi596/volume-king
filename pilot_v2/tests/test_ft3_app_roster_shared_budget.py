"""FT-3 app demand -> shared offline lease with zero actual broker requests."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from pilot_v2.broker_token_status import classify_dhan_token
from pilot_v2.collector_readiness import ProviderCapabilities
from pilot_v2.durable_quote_gate import DurableQuoteGate
from pilot_v2.gateway_contract import plan_demand, INDEXES
from pilot_v2.staged_collector_scheduler import StagedCollectorScheduler

root = Path(__file__).resolve().parents[1] / "android_app" / "src"
def load(name):
    spec = importlib.util.spec_from_file_location("ft3_" + name, root / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

app = load("app_state")
smart = load("smart_data")

def fake_cap(observed):
    """Synthetic positive flags must NOT be confused with observed Oracle."""
    return ProviderCapabilities(observed, True, True, True, False, False, False)

def test_token():
    return classify_dhan_token(now=1000, expires_at=2000,
                               configured=True, renewal_supported=False)

class OwnerDemandToLeaseTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        db = Path(t.name) / "shared-budget.sqlite"
        self.clock = [100.0]
        self.one = StagedCollectorScheduler(DurableQuoteGate(db,clock=lambda:self.clock[0]))
        self.two = StagedCollectorScheduler(DurableQuoteGate(db,clock=lambda:self.clock[0]))

    def demand(self, count):
        locally = app.LocalWatchlists()
        for i in range(count):
            locally.add(i % 5, f"EQ{i:03d}")
        owner_plan = smart.selected_equity_plan(locally)
        self.assertEqual(owner_plan["equity_count"], count)
        self.assertEqual(owner_plan["indices"], INDEXES)
        return plan_demand(locally.groups)

    def test_dynamic_roster_zero_five_fifty_one_seventy(self):
        for n in (0, 5, 51, 70):
            with self.subTest(n=n):
                demand = self.demand(n)
                work = self.one.acquire(demand, fake_cap(False), test_token())
                self.assertFalse(work.readiness.ready)
                self.assertIsNone(work.lease)
                self.assertEqual(work.readiness.reason, "ORACLE_RUNTIME_UNVERIFIED")
        self.assertEqual(self.clock[0], 100.0)

    def test_synthetic_single_budget_for_shared_devices_and_demand(self):
        demand = self.demand(5)
        first = self.one.acquire(demand, fake_cap(True), test_token())
        self.assertIsNotNone(first.lease)
        self.assertEqual({x.kind for x in first.lanes}, {"equity", "index"})
        self.assertEqual(sum(len(x.symbols) for x in first.lanes), 8)
        self.assertIsNone(self.two.acquire(demand, fake_cap(True), test_token()).lease)
        self.one.finish(first)
        self.clock[0] += 1
        next_demand = self.demand(6)
        next_work = self.two.acquire(next_demand, fake_cap(True), test_token())
        self.assertIsNotNone(next_work.lease)
        self.assertEqual(tuple(x.kind for x in next_work.lanes), ("equity",))
        self.assertEqual(next_work.lanes[0].symbols, ("EQ005",))
        self.two.finish(next_work)

    def test_cooldown_and_expired_token_fail_closed(self):
        demand = self.demand(5)
        first = self.one.acquire(demand, fake_cap(True), test_token())
        self.one.finish(first, provider_429_retry_after=90)
        self.clock[0] += 61
        self.assertIsNone(self.two.acquire(demand,fake_cap(True),test_token()).lease)
        expired = classify_dhan_token(now=1000,expires_at=1000,
                     configured=True,renewal_supported=False)
        self.assertIsNone(self.two.acquire(demand,fake_cap(True),expired).lease)

if __name__ == "__main__":
    unittest.main()
