"""Behavioral state transitions for 127-A; no network or credentials."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from login_bootstrap import LoginBootstrapState


class LoginBootstrapTests(unittest.TestCase):
    def test_closed_market_login_and_relogin_are_distinct(self):
        state = LoginBootstrapState()
        self.assertTrue(state.begin(7, authenticated=True))
        self.assertFalse(state.begin(7, authenticated=True))
        self.assertTrue(state.finish(7, "equities", 51, 51))
        self.assertTrue(state.finish(7, "indices", 3, 3))
        self.assertEqual(state.stages, {"equities": "LOADED", "indices": "LOADED"})
        self.assertTrue(state.begin(8, authenticated=True))
        self.assertEqual(state.stages["equities"], "LOADING")
        self.assertEqual(state.stages["indices"], "LOADING")
        self.assertFalse(state.finish(7, "equities", 51, 51))
        self.assertEqual(state.stages["equities"], "LOADING")

    def test_closed_index_recovery_checks_login_generation_not_saved_price(self):
        main=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        poll=main.split("    async def dhan_index_poll():",1)[1].split(
            "    page.run_task(dhan_index_poll)",1)[0]
        self.assertIn('login_bootstrap.generation==provider_generation[0]',poll)
        self.assertIn('login_bootstrap.stages.get("indices")=="LOADED"',poll)
        self.assertIn('login_bootstrap.counts.get("indices")== (3,3)',poll)
        self.assertIn('and not index_loaded_this_login',poll)
        self.assertIn('index_login_recovery_ready=(same_index_login',poll)
        self.assertIn('("PARTIAL","FAILED","COOLDOWN")',poll)
        self.assertIn('and index_login_recovery_ready and not index_loaded_this_login',poll)
        self.assertIn('closed_index_bootstrap_generation[0]=provider_generation[0]',poll)
        self.assertNotIn('quotes.get(sym)',poll)
        self.assertIn('await refresh_dhan_index_quotes(force=True)',poll)
        self.assertIn('and not regular_hours()',poll)

    def test_partial_cannot_be_satisfied_from_old_saved_quote(self):
        state = LoginBootstrapState()
        state.begin(1, authenticated=True)
        state.finish(1, "equities", 40, 51)
        self.assertEqual(state.stages["equities"], "PARTIAL")
        self.assertIn("40/51", state.label("equities"))
        self.assertIn("unverified", state.label("equities"))

    def test_failure_cooldown_and_no_auth(self):
        state = LoginBootstrapState()
        self.assertFalse(state.begin(1, authenticated=False))
        self.assertEqual(state.stages["indices"], "NO AUTH")
        state.begin(2, authenticated=True)
        state.finish(2, "indices", 0, 3, error="HTTP 429")
        self.assertEqual(state.stages["indices"], "COOLDOWN")
        state.finish(2, "equities", 0, 51, error="Connection failed")
        self.assertEqual(state.stages["equities"], "FAILED")
        self.assertFalse(state.finish(1, "equities", 51, 51))
        state.begin(3, authenticated=False)
        self.assertEqual(state.counts, {})
        self.assertEqual(state.stages["equities"], "NO AUTH")


if __name__ == "__main__":
    unittest.main()
