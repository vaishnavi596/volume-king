import unittest

from v3_doctor_repairs import (COOLDOWN_SECONDS, MAX_ATTEMPTS_PER_GENERATION,
                               STUCK_AFTER_SECONDS, RepairLedger, StuckFlagWatch)


def finding(action="release_busy_flag", target="scan_busy", fid="BK-DOC-STUCK"):
    return {"id": fid, "action": action, "target": target, "preview": "x"}


class StuckFlagTests(unittest.TestCase):
    def test_flag_is_stuck_only_after_limit_and_resets_when_cleared(self):
        watch = StuckFlagWatch()
        watch.sample({"scan_busy": True, "ok": False}, 100)
        self.assertEqual(watch.stuck(100 + STUCK_AFTER_SECONDS - 1), [])
        self.assertEqual(watch.stuck(100 + STUCK_AFTER_SECONDS), ["scan_busy"])
        watch.sample({"scan_busy": False, "ok": False}, 500)
        self.assertEqual(watch.stuck(10_000), [])

    def test_per_flag_limit_protects_long_legitimate_work(self):
        watch = StuckFlagWatch()
        watch.sample({"hist": True, "opt": True}, 0)
        limits = {"hist": 1200, "opt": 120}
        self.assertEqual(watch.stuck(300, limits=limits), ["opt"])
        self.assertEqual(watch.stuck(1200, limits=limits), ["hist", "opt"])

    def test_bad_inputs_are_ignored(self):
        watch = StuckFlagWatch()
        watch.sample(None, 1)
        watch.sample({"a": True}, float("nan"))
        self.assertEqual(watch.stuck(float("inf")), [])


class LedgerTests(unittest.TestCase):
    def test_only_allowlisted_actions_are_proposed(self):
        ledger = RepairLedger()
        bad = [finding(action="rotate_token"), finding(action="place_order"),
               finding(action="edit_settings"), {"action": "release_busy_flag"}, "x"]
        self.assertEqual(ledger.propose(bad, 1, 1000.0), [])
        self.assertEqual(len(ledger.propose([finding()], 1, 1000.0)), 1)

    def test_cap_and_cooldown_per_generation(self):
        ledger = RepairLedger()
        now = 1000.0
        for i in range(MAX_ATTEMPTS_PER_GENERATION):
            plan = ledger.propose([finding()], 1, now)[0]
            ledger.record(plan, 1, now, ok=False, detail="still stuck")
            self.assertEqual(ledger.propose([finding()], 1, now + 1), [])  # cooling down
            now += COOLDOWN_SECONDS + 1
        self.assertEqual(ledger.propose([finding()], 1, now), [])          # cap reached
        self.assertEqual(len(ledger.propose([finding()], 2, now)), 1)      # new generation

    def test_audit_never_claims_tokens_or_orders(self):
        ledger = RepairLedger()
        plan = ledger.propose([finding()], 1, 5.0)[0]
        ledger.record(plan, 1, 5.0, ok=True, detail="released")
        report = ledger.report()
        event = report["events"][0]
        self.assertEqual((event["result"], event["tokens_touched"], event["orders_sent"]),
                         ("RETEST_OK", False, 0))
        self.assertEqual(report["orders_sent"], 0)
        self.assertNotIn("rotate_token", report["allowed_actions"])

    def test_invalid_generation_or_time_proposes_nothing(self):
        ledger = RepairLedger()
        self.assertEqual(ledger.propose([finding()], True, 1.0), [])
        self.assertEqual(ledger.propose([finding()], 1, float("nan")), [])


if __name__ == "__main__":
    unittest.main()
