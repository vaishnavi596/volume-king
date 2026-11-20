"""Static regression gates for the combined B3 scanner pacing patch."""
import ast
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
AUTO=SOURCE.split("    async def auto_scan_loop(generation):",1)[1].split("    scan_live.on_change=auto_scan_changed",1)[0]

class ScannerBatchGuards(unittest.TestCase):
    def test_source_compiles(self):
        ast.parse(SOURCE)
    def test_shared_queue_does_not_erase_selected_deadline(self):
        busy=AUTO.split('if prefs.get("source")=="Dhan" and dhan_history_scan_active[0]:',1)[1].split('if prefs.get("source")=="Dhan" and not dhan_feed.connected:',1)[0]
        self.assertNotIn("scan_next_refresh[0]=None",busy)
        self.assertIn("await asyncio.sleep(5)",busy)
    def test_closed_market_does_not_force_page_rebuild(self):
        closed=AUTO.split("if not refresh_hours():",1)[1].split("continue",1)[0]
        self.assertNotIn("request_view_refresh",closed)
        self.assertNotIn("page.update()",closed)
    def test_selection_repaint_deferred(self):
        selected=SOURCE.split("    def trigger_scan(e=None):",1)[1].split("    for c in [scan_symbol",1)[0]
        self.assertIn("if current[0]==3:request_view_refresh(3)",selected)
        self.assertNotIn("if current[0]==3:select(3)",selected)
    def test_auto_off_and_stale_refresh_guards(self):
        self.assertIn("if scan_live.value:\n        page.run_task(auto_scan_loop",SOURCE)
        self.assertIn("if target is None or target!=current[0]:return",SOURCE)

if __name__=="__main__":
    unittest.main()
