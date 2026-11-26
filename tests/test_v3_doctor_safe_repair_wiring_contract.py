import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1].joinpath("src", "main.py").read_text(encoding="utf-8")


class DoctorSafeRepairWiring(unittest.TestCase):
    def block(self):
        start = SRC.index("# ---- J5: bounded, allowlisted on-phone self-repair")
        text = SRC[start:SRC.index("repair_board_signature=[None]")]
        return text.split("\n", 1)[1]  # drop the descriptive header comment

    def test_auto_repair_defaults_off_and_is_user_switchable(self):
        self.assertIn('prefs.get("doctor_auto_repair",False)', SRC)
        self.assertIn("Doctor auto-repair (safe, bounded)", SRC)
        self.assertIn("page.run_task(doctor_auto_repair_poll)", SRC)

    def test_repair_block_never_touches_tokens_keys_orders_or_settings(self):
        block = self.block().lower()
        for forbidden in ("token", "secret", "place_order", "renew", "prefs[", "save()",
                          "disconnect", "access_key", "live_orders"):
            self.assertNotIn(forbidden, block, forbidden)

    def test_only_allowlisted_actions_are_executed(self):
        block = self.block()
        for action in ("release_busy_flag", "retry_closed_index_snapshot", "retry_missing_hist"):
            self.assertIn(action, block)
        self.assertIn("doctor_repair_ledger.propose(", block)
        self.assertIn("doctor_repair_ledger.record(", block)

    def test_master_diag_includes_repair_ledger(self):
        self.assertEqual(SRC.count('"doctor_safe_repairs":doctor_repair_ledger.report()'), 1)
        self.assertEqual(SRC.count('data["doctor_safe_repairs"]'), 1)


if __name__ == "__main__":
    unittest.main()
