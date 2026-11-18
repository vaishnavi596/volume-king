"""S1 staged work leases: synthetic provider evidence only, no network."""
import tempfile
import unittest
from pathlib import Path
from pilot_v2.collector_readiness import ProviderCapabilities
from pilot_v2.broker_token_status import classify_dhan_token
from pilot_v2.durable_quote_gate import DurableQuoteGate
from pilot_v2.staged_collector_scheduler import StagedCollectorScheduler
from pilot_v2.gateway_contract import plan_demand, ContractError

def cap(observed=True,eq=True,idx=True,auth=True):
    return ProviderCapabilities(observed,auth,eq,idx,False,False,False)

def token(expires=2000):
    return classify_dhan_token(now=1000,expires_at=expires,
                               configured=True,renewal_supported=False)

class StagedCollectorTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        path=Path(d.name)/"one.sqlite"
        self.t=[100.]
        self.one=StagedCollectorScheduler(DurableQuoteGate(path,clock=lambda:self.t[0]))
        self.two=StagedCollectorScheduler(DurableQuoteGate(path,clock=lambda:self.t[0]))

    def demand(self,*equities):
        return plan_demand([list(equities),[],[],[],[]])

    def test_no_oracle_evidence_cannot_acquire_any_lease(self):
        work=self.one.acquire(self.demand("TCS"),cap(observed=False),token())
        self.assertFalse(work.readiness.ready)
        self.assertIsNone(work.lease)
        self.assertEqual(work.lanes,())

    def test_two_workers_share_one_quote_budget(self):
        work=self.one.acquire(self.demand("TCS"),cap(),token())
        self.assertIsNotNone(work.lease)
        self.assertEqual({x.kind for x in work.lanes},{"equity","index"})
        other=self.two.acquire(self.demand("TCS"),cap(),token())
        self.assertIsNone(other.lease)
        self.one.finish(work)
        self.t[0]+=1
        self.assertIsNone(self.two.acquire(self.demand("TCS"),cap(),token()).lease)
        self.t[0]+=59
        again=self.two.acquire(self.demand("TCS"),cap(),token())
        self.assertIsNotNone(again.lease)
        self.two.finish(again)

    def test_new_equity_does_not_resend_cached_index(self):
        first=self.one.acquire(self.demand("TCS"),cap(),token())
        self.one.finish(first)
        self.t[0]+=1
        other=self.two.acquire(self.demand("TCS","INFY"),cap(),token())
        self.assertEqual(len(other.lanes),1)
        self.assertEqual(other.lanes[0].kind,"equity")
        self.assertEqual(other.lanes[0].symbols,("INFY",))
        self.two.finish(other)

    def test_429_blocks_second_mobile_until_cooldown(self):
        first=self.one.acquire(self.demand("TCS"),cap(),token())
        self.one.finish(first,provider_429_retry_after=90)
        self.t[0]+=60
        self.assertIsNone(self.two.acquire(self.demand("TCS"),cap(),token()).lease)
        self.t[0]+=30
        next_work=self.two.acquire(self.demand("TCS"),cap(),token())
        self.assertIsNotNone(next_work.lease)
        self.two.finish(next_work)

    def test_no_auth_and_missing_entitlement_fail_closed(self):
        for c,t in ((cap(auth=False),token()),
                    (cap(eq=False),token()),
                    (cap(),token(expires=1000))):
            with self.subTest(c=c,t=t):
                w=self.one.acquire(self.demand("TCS"),c,t)
                self.assertIsNone(w.lease)

    def test_zero_equity_keeps_independent_index_lane(self):
        w=self.one.acquire(self.demand(),cap(eq=False),token())
        self.assertEqual([x.kind for x in w.lanes],["index"])
        self.assertEqual(len(w.lanes[0].symbols),3)
        self.one.finish(w)

    def test_cannot_finish_without_active_lease(self):
        blocked=self.one.acquire(self.demand(),cap(observed=False),token())
        with self.assertRaises(ContractError):
            self.one.finish(blocked)

if __name__=="__main__":
    unittest.main()
