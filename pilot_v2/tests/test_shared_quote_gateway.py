"""Shared V2 read-only 1–3 phone fanout: OFFLINE no broker/socket requests."""
import unittest
from pilot_v2.device_policy import DeviceRegistry
from pilot_v2.device_sessions import DeviceSessionGateway, VerifiedDevice, SessionDenied
from pilot_v2.gateway_contract import plan_demand, ContractError
from pilot_v2.shared_quote_gateway import SharedQuoteGateway

MASTER="master_device_000001"
SECOND="second_device_00001"
THIRD="third_device_000001"

def snapshot(revision, quotes):
    return {"protocol":"botking-v2-readonly","source":"dhan",
            "live_orders_enabled":False,"freshness":"unverified",
            "revision":revision,"quotes":quotes}

class SharedQuoteGatewayTests(unittest.TestCase):
    def setUp(self):
        self.registry=DeviceRegistry()
        self.registry.enroll_master(MASTER,verified_bootstrap=True)
        self.gateway=DeviceSessionGateway(
            self.registry,lambda proof: VerifiedDevice(proof),
            clock=lambda:100.,ttl_seconds=300)
        self.master=self.gateway.issue(MASTER)
        self.shared=SharedQuoteGateway(self.gateway)

    def test_two_or_three_phones_read_same_cache_without_provider_calls(self):
        self.gateway.assign(self.master,SECOND,{"quotes"})
        self.gateway.assign(self.master,THIRD,{"quotes","indices"})
        s2=self.gateway.issue(SECOND)
        s3=self.gateway.issue(THIRD)
        self.shared.select_equities(self.master,[["RELIANCE"],[],[],[],[]])
        self.shared.select_equities(s2,[["TCS"],[],[],[],[]])
        self.shared.select_equities(s3,[["RELIANCE","TCS"],[],[],[],[]])
        plan=plan_demand([["RELIANCE","TCS"],[],[],[],[]])
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            1,{"RELIANCE":2000,"TCS":3000,"NIFTY":25000}),plan))
        self.assertEqual(set(self.shared.read(self.master,"quotes")["quotes"]),{"RELIANCE"})
        self.assertEqual(set(self.shared.read(s2,"quotes")["quotes"]),{"TCS"})
        self.assertEqual(set(self.shared.read(s3,"quotes")["quotes"]),{"RELIANCE","TCS"})
        self.assertEqual(set(self.shared.read(s3,"indices")["quotes"]),{"NIFTY"})
        with self.assertRaises(SessionDenied):
            self.shared.read(s2,"indices")
        self.assertFalse(hasattr(self.shared,"dhan_feed"))
        self.assertFalse(hasattr(self.shared,"http_client"))

    def test_selection_changes_do_not_leak_or_drop_shared_price(self):
        self.shared.select_equities(self.master,[["RELIANCE","TCS"],[],[],[],[]])
        plan=plan_demand([["RELIANCE","TCS"],[],[],[],[]])
        self.shared.publish_from_trusted_collector(snapshot(1,{"RELIANCE":10,"TCS":20}),plan)
        self.shared.select_equities(self.master,[["TCS"],[],[],[],[]])
        rows=self.shared.read(self.master,"quotes")["quotes"]
        self.assertEqual(set(rows),{"TCS"})
        rows["TCS"]["price"]=9999
        self.assertEqual(self.shared.read(self.master,"quotes")["quotes"]["TCS"]["price"],20)

    def test_revoked_device_cannot_read_old_cached_data(self):
        self.gateway.assign(self.master,SECOND,{"quotes"})
        s2=self.gateway.issue(SECOND)
        self.shared.select_equities(s2,[["TCS"],[],[],[],[]])
        self.shared.publish_from_trusted_collector(
            snapshot(1,{"TCS":20}),plan_demand([["TCS"],[],[],[],[]]))
        self.gateway.assign(self.master,SECOND,{"quotes"},enabled=False)
        with self.assertRaises(SessionDenied):
            self.shared.read(s2,"quotes")

    def test_stale_partial_and_invalid_collector_payloads(self):
        self.shared.select_equities(self.master,[["RELIANCE","TCS"],[],[],[],[]])
        plan=plan_demand([["RELIANCE","TCS"],[],[],[],[]])
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            1,{"RELIANCE":100,"TCS":200}),plan))
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(2,{"TCS":220}),plan))
        self.assertFalse(self.shared.publish_from_trusted_collector(snapshot(1,{"TCS":1}),plan))
        self.assertEqual(self.shared.read(self.master,"quotes")["quotes"]["RELIANCE"]["price"],100)
        with self.assertRaises(ContractError):
            self.shared.publish_from_trusted_collector(snapshot(3,{"TCS":False}),plan)
        self.assertEqual(self.shared.read(self.master,"quotes")["revision"],2)

    def test_zero_five_fifty_one_seventy_and_invalid_access(self):
        for n in (0,5,51,70):
            symbols=[f"EQ{i:03d}" for i in range(n)]
            self.assertEqual(self.shared.select_equities(self.master,
                [symbols,[],[],[],[]]),n)
        with self.assertRaises(ContractError):
            self.shared.select_equities(self.master,
                [[f"EQ{i:03d}" for i in range(71)],[],[],[],[]])
        with self.assertRaises(SessionDenied):
            self.shared.read(self.master,"options")

if __name__=="__main__":
    unittest.main()
