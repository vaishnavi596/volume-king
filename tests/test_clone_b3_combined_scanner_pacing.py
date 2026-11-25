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
    def test_cache_only_scan_can_run_without_dhan_login(self):
        scan=SOURCE.split("    async def scan_market(allow_network=True):",1)[1].split("        generation=scan_generation[0]",1)[0]
        self.assertIn('not dhan_feed.connected and allow_network',scan)
        self.assertIn('if not allow_network and prefs.get("source")=="Dhan":',SOURCE)
    def test_watchlist_filtered_membership_matches_row_eligibility(self):
        rows=SOURCE.split("                    def filtered_member(sym):",1)[1].split("                    membership=",1)[0]
        for check in ('signal.get("timeframe")=="3m"',
                      'signal.get("source")==expected_source',
                      'search.value.upper() not in sym'):
            self.assertIn(check,rows)
        membership=SOURCE.split("                    membership=tuple(",1)[1].split("                else:",1)[0]
        # Membership rebuild must invalidate both mounted price and evidence.
        self.assertIn("if membership!=last_filtered_membership[0]:",membership)
        for guard in ("last_cell_signatures.clear()", "last_evidence_signatures.clear()"):
            self.assertIn(guard,membership)
            self.assertLess(membership.index(guard),membership.index("fill_watch()"))
        self.assertIn("if watch_list.page is not None:watch_list.update()",membership)
    def test_index_batch_invalid_payload_uses_safe_fallback(self):
        index=SOURCE.split("snapshots=await asyncio.to_thread(dhan_feed.index_batch_quotes)",1)[1].split("missing_indices=",1)[0]
        self.assertIn("if not isinstance(snapshots,dict):",index)
        self.assertIn("snapshots={}",index)
        self.assertIn('("NIFTY","BANKNIFTY","SENSEX")',SOURCE)
    def test_option_metrics_reject_nonfinite_and_boolean_values(self):
        options=SOURCE.split("    def scanner_option_context():",1)[1].split("    def scanner():",1)[0]
        for check in ('isinstance(data.get("pcr"),bool)',
                      'math.isfinite(data["pcr"])',
                      'isinstance(data.get("max_pain"),bool)',
                      'math.isfinite(data["max_pain"])',
                      'data.get("signal_eligible") is not False'):
            self.assertIn(check,options)
    def test_auto_off_and_stale_refresh_guards(self):
        self.assertIn("if scan_live.value:\n        page.run_task(auto_scan_loop",SOURCE)
        self.assertIn("if target is None or target!=current[0] or not app_active[0] or lifecycle_background[0]:return",SOURCE)

if __name__=="__main__":
    unittest.main()
