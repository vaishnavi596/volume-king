"""Offline, synthetic V2 pilot contract and four-device management tests."""
import unittest
from pilot_v2.gateway_contract import (ContractError, BrokerState, RevisionCache,
                                       plan_demand, INDEXES)
from pilot_v2.device_policy import (DeviceRegistry, DevicePolicyError,
                                    ALLOWED_FEEDS)

MASTER="master_device_000001"
SECOND="second_device_00001"
THIRD="third_device_000001"
FOURTH="fourth_device_000001"
FIFTH="fifth_device_0000001"

class PilotV2Tests(unittest.TestCase):
    def test_zero_five_fifty_one_seventy_and_indexes(self):
        for n in (0,5,51,70):
            with self.subTest(n=n):
                xs=[f"EQ{i:03d}" for i in range(n)]
                d=plan_demand([xs[:n//2], xs[n//2:], [], [], []])
                self.assertEqual(len(d.equities),n)
                self.assertEqual(d.indices, INDEXES)

    def test_duplicate_and_71_fail(self):
        for g in ([["TCS"],["TCS"],[],[],[]],
                  [[f"EQ{i:03d}" for i in range(71)],[],[],[],[]],
                  [["NIFTY"],[],[],[],[]],
                  [[[1]],[],[],[],[]]):
            with self.assertRaises(ContractError):
                plan_demand(g)

    def test_revisions_partial_stale_and_invalid_fail_closed(self):
        c=RevisionCache()
        d=plan_demand([["TCS","INFY"],[],[],[],[]])
        p={"protocol":"botking-v2-readonly","source":"dhan",
           "live_orders_enabled":False,"freshness":"unverified",
           "revision":1,"quotes":{"TCS":100,"INFY":200}}
        self.assertTrue(c.update(p,d))
        self.assertTrue(c.update(dict(p,revision=2,quotes={"TCS":110}),d))
        self.assertFalse(c.update(p,d))
        self.assertEqual(c.rows["INFY"]["price"],200)
        self.assertFalse(c.rows["TCS"]["live_verified"])
        with self.assertRaises(ContractError):
            c.update(dict(p,revision=3,quotes={"TCS":False}),d)
        self.assertEqual(c.revision,2)

    def test_dhan_and_app_sessions_are_distinct(self):
        self.assertTrue(BrokerState(True,"CONNECTED").data_ready)
        self.assertFalse(BrokerState(True,"REAUTH_REQUIRED").data_ready)
        self.assertFalse(BrokerState(False,"CONNECTED").data_ready)

    def test_master_controls_four_device_access(self):
        reg=DeviceRegistry()
        with self.assertRaises(DevicePolicyError):
            reg.enroll_master(MASTER)
        reg.enroll_master(MASTER,verified_bootstrap=True)
        reg.assign(MASTER,SECOND,{"quotes","indices"})
        reg.assign(MASTER,THIRD,{"candles"})
        self.assertTrue(reg.can_access(SECOND,"quotes"))
        self.assertFalse(reg.can_access(SECOND,"options"))
        self.assertTrue(reg.can_access(THIRD,"candles"))
        reg.assign(MASTER,FOURTH,{"quotes"})
        self.assertTrue(reg.can_access(FOURTH,"quotes"))
        with self.assertRaises(DevicePolicyError):
            reg.assign(MASTER,FIFTH,{"quotes"})
        with self.assertRaises(DevicePolicyError):
            reg.assign(SECOND,THIRD,{"options"})
        reg.assign(MASTER,SECOND,{"quotes"},enabled=False)
        self.assertFalse(reg.can_access(SECOND,"quotes"))
        reg.revoke(MASTER,THIRD)
        self.assertFalse(reg.can_access(THIRD,"candles"))
        self.assertEqual(len(reg.grants),3)
        with self.assertRaises(DevicePolicyError):
            reg.revoke(SECOND,MASTER)
        with self.assertRaises(DevicePolicyError):
            reg.assign(MASTER,SECOND,{"credentials"})
        self.assertEqual(reg.grants[SECOND].feeds,frozenset({"quotes"}))
        self.assertTrue(reg.can_access(FOURTH,"quotes"))
        self.assertEqual(reg.grants[MASTER].feeds,ALLOWED_FEEDS)

if __name__=="__main__":
    unittest.main()
