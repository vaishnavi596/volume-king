"""Read-only first-login bootstrap contract; no network or broker access."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from login_bootstrap import LoginBootstrapState


class LoginBootstrapBehaviorTests(unittest.TestCase):
    def test_generation_is_idempotent_and_stale_results_cannot_override_new_login(self):
        state = LoginBootstrapState()
        self.assertFalse(state.begin(1, authenticated=False))
        self.assertEqual(state.stages, {"equities": "NO AUTH", "indices": "NO AUTH"})
        self.assertTrue(state.begin(1, authenticated=True))
        self.assertEqual(state.stages, {"equities": "LOADING", "indices": "LOADING"})
        self.assertTrue(state.finish(1, "equities", 51, 51))
        self.assertFalse(state.begin(1, authenticated=True))
        self.assertEqual(state.stages["equities"], "LOADED")
        self.assertTrue(state.begin(2, authenticated=True))
        self.assertEqual(state.stages["equities"], "LOADING")
        self.assertFalse(state.finish(1, "indices", 3, 3))
        self.assertEqual(state.stages["indices"], "LOADING")

    def test_partial_equities_and_independent_indices(self):
        state = LoginBootstrapState()
        state.begin(4, authenticated=True)
        self.assertTrue(state.finish(4, "equities", 49, 51))
        self.assertEqual(state.stages["equities"], "PARTIAL")
        self.assertEqual(state.counts["equities"], (49, 51))
        self.assertEqual(state.stages["indices"], "LOADING")
        self.assertTrue(state.finish(4, "indices", 3, 3))
        self.assertEqual(state.stages["indices"], "LOADED")
        self.assertIn("49/51", state.label("equities"))
        self.assertIn("exchange time unverified", state.label("indices"))

    def test_cooldown_and_failure_never_become_loaded(self):
        state = LoginBootstrapState()
        state.begin(5, authenticated=True)
        state.finish(5, "equities", 0, 51, error="HTTP 429")
        state.finish(5, "indices", 0, 3, error="upstream failed")
        self.assertEqual(state.stages["equities"], "COOLDOWN")
        self.assertEqual(state.stages["indices"], "FAILED")
        self.assertTrue(state.begin(6, authenticated=True))
        self.assertEqual(state.counts, {})
        self.assertEqual(state.stages["equities"], "LOADING")
        state.begin(6, authenticated=False)
        self.assertEqual(state.stages, {"equities": "NO AUTH", "indices": "NO AUTH"})

    def test_reject_invalid_or_unknown_stage_counts(self):
        state = LoginBootstrapState()
        state.begin(7, authenticated=True)
        self.assertFalse(state.finish(7, "options", 1, 1))
        # Empty selected equities are an intentional SKIPPED stage, not a malformed count.
        for received, expected in ((-1, 51), (52, 51), (True, 1), (1, True), (False, 51), (0, False)):
            with self.subTest(received=received, expected=expected):
                with self.assertRaises(ValueError):
                    state.finish(7, "equities", received, expected)
        self.assertEqual(state.stages["equities"], "LOADING")


if __name__ == "__main__":
    unittest.main()
