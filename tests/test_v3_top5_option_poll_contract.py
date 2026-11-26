import pathlib
import re
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


def worker_text():
    text = SRC.read_text(encoding="utf-8")
    start = text.index("    async def top5_option_poll():")
    end = text.index("    def selected_option_rows():", start)
    return text, text[start:end]


class Top5OptionPollContract(unittest.TestCase):
    def test_worker_started_once(self):
        text, _ = worker_text()
        self.assertEqual(text.count("page.run_task(top5_option_poll)"), 1)

    def test_worker_yields_to_shared_gates(self):
        _, body = worker_text()
        for needle in ("app_active[0]", "lifecycle_background[0]", "option_feed_busy[0]",
                       "dhan_history_scan_active[0]", "regular_hours()",
                       'cooldown_remaining("/dhan/option-expiries")',
                       'cooldown_remaining("/dhan/option-chain")'):
            self.assertIn(needle, body)

    def test_worker_is_read_only_and_does_not_touch_ui_chain_state(self):
        _, body = worker_text()
        for forbidden in ("dhan_option_metrics", "market_store.put", "option_feed_status",
                          "expiry.value", "request_view_refresh", "place_order", "paper_"):
            self.assertNotIn(forbidden, body)
        self.assertIn("finally:\n                    option_feed_busy[0]=False", body)

    def test_worker_pacing_and_scope(self):
        _, body = worker_text()
        self.assertIn("asyncio.sleep(8)", body)
        self.assertIn("asyncio.sleep(3.25)", body)
        self.assertIn("[:5]", body)  # Super Five candidates only, never 70 symbols
        self.assertRegex(body, r"chain_age\(sym\)>45")
        self.assertIn('data.get("signal_eligible") is not False', body)
        self.assertIn('data["observed_at"]=time.time()', body)
        self.assertIsNone(re.search(r"for\s+\w+\s+in\s+selected_equities", body))


if __name__ == "__main__":
    unittest.main()
