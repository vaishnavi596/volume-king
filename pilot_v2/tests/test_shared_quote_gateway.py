"""Shared V2 read-only 1–3 phone fanout: OFFLINE no broker/socket requests."""
import unittest
import sys
from pathlib import Path
from pilot_v2.device_policy import DeviceRegistry
from pilot_v2.device_sessions import DeviceSessionGateway, VerifiedDevice, SessionDenied
from pilot_v2.gateway_contract import plan_demand, ContractError, Demand
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

    def test_uninitialized_collector_never_emits_invalid_mobile_envelope(self):
        self.shared.select_equities(self.master, [["TCS"], [], [], [], []])
        with self.assertRaisesRegex(ContractError, "No validated collector snapshot"):
            self.shared.read(self.master, "quotes")
        with self.assertRaisesRegex(ContractError, "No validated collector snapshot"):
            self.shared.read(self.master, "indices")
        self.assertEqual(self.shared.union_demand().equities, ("TCS",))
        with self.assertRaises(SessionDenied):
            self.shared.read("invalid", "quotes")

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

    def test_global_union_deduplicates_three_phones_and_three_indexes(self):
        self.gateway.assign(self.master,SECOND,{"quotes"})
        self.gateway.assign(self.master,THIRD,{"quotes"})
        s2=self.gateway.issue(SECOND)
        s3=self.gateway.issue(THIRD)
        self.shared.select_equities(self.master,[["RELIANCE","TCS"],[],[],[],[]])
        self.shared.select_equities(s2,[["TCS"],[],[],[],[]])
        self.shared.select_equities(s3,[["RELIANCE"],[],[],[],[]])
        plan=self.shared.union_demand()
        self.assertEqual(plan.equities,("RELIANCE","TCS"))
        self.assertEqual(plan.indices,("NIFTY","BANKNIFTY","SENSEX"))
        self.assertEqual(len(plan.equities),2)

    def test_combined_seventy_cap_is_atomic_and_disabling_removes_demand(self):
        self.gateway.assign(self.master,SECOND,{"quotes"})
        s2=self.gateway.issue(SECOND)
        sixty=[f"EQ{i:03d}" for i in range(60)]
        fifteen=[f"EQ{i:03d}" for i in range(60,75)]
        self.shared.select_equities(self.master,[sixty,[],[],[],[]])
        with self.assertRaises(ContractError):
            self.shared.select_equities(s2,[fifteen,[],[],[],[]])
        self.assertEqual(len(self.shared.union_demand().equities),60)
        # Ten overlapping or new symbols fit the owner's one shared cap.
        self.shared.select_equities(s2,[fifteen[:10],[],[],[],[]])
        self.assertEqual(len(self.shared.union_demand().equities),70)
        self.gateway.assign(self.master,SECOND,{"quotes"},enabled=False)
        self.assertEqual(len(self.shared.union_demand().equities),60)
        self.gateway.assign(self.master,SECOND,{"quotes"},enabled=True)
        self.assertEqual(len(self.shared.union_demand().equities),60)
        s2new=self.gateway.issue(SECOND)
        self.shared.select_equities(s2new,[["EQ070"],[],[],[],[]])
        self.assertEqual(len(self.shared.union_demand().equities),61)

    def test_zero_selection_yields_zero_equity_work_plus_three_indices(self):
        self.shared.select_equities(self.master,[[],[],[],[],[]])
        self.assertEqual(self.shared.union_demand().equities,())
        self.assertEqual(len(self.shared.union_demand().indices),3)

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

    def test_evidenced_collector_rows_preserve_last_good_across_mixed_revisions(self):
        self.shared.select_equities(self.master, [["TCS", "INFY"], [], [], [], []])
        plan = plan_demand([["TCS", "INFY"], [], [], [], []])
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            10, {"TCS": {"price": 120, "revision": 10},
                 "INFY": {"price": 200, "revision": 8}}), plan))
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            11, {"TCS": {"price": 99, "revision": 9},
                 "INFY": {"price": 205, "revision": 11}}), plan))
        result = self.shared.read(self.master, "quotes")
        self.assertEqual(result["revision"], 11)
        self.assertEqual(result["quotes"]["TCS"]["price"], 120.0)
        self.assertEqual(result["quotes"]["TCS"]["revision"], 10)
        self.assertEqual(result["quotes"]["INFY"]["price"], 205.0)
        self.assertEqual(result["quotes"]["INFY"]["revision"], 11)
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            12, {"TCS": {"price": 1, "revision": 10},
                 "INFY": {"price": 1, "revision": 11}}), plan))
        self.assertEqual(self.shared.read(self.master, "quotes")["quotes"],
                         result["quotes"])
        with self.assertRaises(ContractError):
            self.shared.publish_from_trusted_collector(snapshot(
                13, {"TCS": {"price": 500, "revision": 13},
                     "INFY": {"price": 100, "revision": 14}}), plan)
        self.assertEqual(self.shared.read(self.master, "quotes")["revision"], 12)
        src = Path(__file__).resolve().parents[1] / "android_app" / "src"
        sys.path.insert(0, str(src))
        from feed_inbox import DeviceFeedInbox
        device = DeviceFeedInbox()
        self.assertTrue(device.apply_feed("quotes", result, ("TCS", "INFY")))
        self.assertEqual(device.visible("TCS", ("TCS", "INFY"))["revision"], 10)

    def test_symbol_revision_provenance_cannot_downgrade_to_numeric(self):
        self.shared.select_equities(self.master, [["TCS", "INFY"], [], [], [], []])
        plan = plan_demand([["TCS", "INFY"], [], [], [], []])
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            5, {"TCS": {"price": 100, "revision": 5}, "INFY": 200}), plan))
        before = self.shared.read(self.master, "quotes")
        with self.assertRaisesRegex(ContractError, "revision downgrade"):
            self.shared.publish_from_trusted_collector(snapshot(
                6, {"TCS": 1, "INFY": 210}), plan)
        self.assertEqual(self.shared.read(self.master, "quotes"), before)
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            6, {"TCS": {"price": 110, "revision": 6}, "INFY": 210}), plan))
        latest = self.shared.read(self.master, "quotes")
        self.assertEqual(latest["quotes"]["TCS"]["price"], 110.0)
        self.assertEqual(latest["quotes"]["INFY"]["price"], 210.0)
        with self.assertRaises(ContractError):
            self.shared.publish_from_trusted_collector(snapshot(
                7, {"TCS": {"price": 111, "revision": True}}), plan)
        self.assertEqual(self.shared.read(self.master, "quotes"), latest)

    def test_collector_rejects_secret_or_bad_schema_without_cache_mutation(self):
        self.shared.select_equities(self.master, [["TCS"], [], [], [], []])
        plan = plan_demand([["TCS"], [], [], [], []])
        self.assertTrue(self.shared.publish_from_trusted_collector(snapshot(
            3, {"TCS": {"price": 100, "revision": 3}}), plan))
        baseline = self.shared.read(self.master, "quotes")
        for bad in (dict(snapshot(4, {"TCS": 120}), access_token="private"),
                    dict(snapshot(4, {"TCS": 120}), schema_version=True),
                    dict(snapshot(4, {"TCS": 120}), schema_version=2),
                    dict(snapshot(4, {"TCS": 120}), missing="field")):
            with self.subTest(fields=tuple(sorted(bad))), self.assertRaises(ContractError):
                self.shared.publish_from_trusted_collector(bad, plan)
            self.assertEqual(self.shared.read(self.master, "quotes"), baseline)
        good = dict(snapshot(4, {"TCS": {"price": 120, "revision": 4}}),
                    schema_version=1)
        self.assertTrue(self.shared.publish_from_trusted_collector(good, plan))
        self.assertEqual(self.shared.read(self.master, "quotes")["quotes"]["TCS"]["price"], 120.0)

    def test_collector_cannot_expand_global_demand_or_change_indexes(self):
        self.shared.select_equities(self.master, [["TCS"], [], [], [], []])
        actual = self.shared.union_demand()
        self.assertEqual(actual.equities, ("TCS",))
        for unauthorized in (
                Demand(("TCS", "INFY")),
                Demand(("TCS",), ("NIFTY",)),
                Demand(tuple("EQ" + str(i) for i in range(71))),
                Demand(("TCS", "TCS")),
                Demand(("TCS",), ("NIFTY", "BANKNIFTY", "FAKE"))):
            with self.subTest(demand=repr(unauthorized)), self.assertRaises(ContractError):
                self.shared.publish_from_trusted_collector(
                    snapshot(1, {"TCS": 100, "INFY": 200}), unauthorized)
        with self.assertRaises(ContractError):
            self.shared.read(self.master, "quotes")
        self.assertTrue(self.shared.publish_from_trusted_collector(
            snapshot(1, {"TCS": 100, "NIFTY": 25000}), actual))
        self.assertEqual(set(self.shared.read(self.master, "quotes")["quotes"]), {"TCS"})
        self.assertEqual(set(self.shared.read(self.master, "indices")["quotes"]), {"NIFTY"})

    def test_shared_read_contract_is_accepted_by_actual_flet_inbox(self):
        """The same quote/index read payload must pass the Android-side schema."""
        src=Path(__file__).resolve().parents[1]/"android_app"/"src"
        sys.path.insert(0,str(src))
        from feed_inbox import DeviceFeedInbox
        inbox=DeviceFeedInbox()
        self.gateway.assign(self.master,SECOND,{"quotes","indices"})
        delegated=self.gateway.issue(SECOND)
        self.shared.select_equities(delegated,[["TCS"],[],[],[],[]])
        self.shared.publish_from_trusted_collector(
            snapshot(1,{"TCS":100,"NIFTY":25000}),
            plan_demand([["TCS"],[],[],[],[]]))
        quotes=self.shared.read(delegated,"quotes")
        indexes=self.shared.read(delegated,"indices")
        self.assertEqual(quotes["schema_version"],1)
        self.assertEqual(indexes["schema_version"],1)
        self.assertTrue(inbox.apply_feed("quotes",quotes,("TCS",)))
        self.assertTrue(inbox.apply_feed("indices",indexes,("TCS",)))
        self.assertEqual(inbox.visible("TCS",("TCS",))["price"],100.0)
        self.assertEqual(inbox.visible("NIFTY",())["price"],25000.0)
        self.assertEqual(inbox.visible("TCS",())["status"],"WAIT")
        self.assertIn("HIST (unverified)",inbox.display("NIFTY",()))
        self.assertFalse(inbox.apply_feed("quotes",quotes,("TCS",)))

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
