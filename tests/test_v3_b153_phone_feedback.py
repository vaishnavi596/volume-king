"""B153 phone feedback: 17 default, independent timeframe, non-blocking pages, truthful Doctor."""
import ast
import unittest
from pathlib import Path
from test_audit import start
from scanner_engine import ALL_FILTERS

ROOT=Path(__file__).resolve().parents[1]
MAIN=(ROOT/"src"/"main.py").read_text(encoding="utf-8")

class V3B153PhoneFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ast.parse(MAIN)

    def test_first_install_has_17_filters_and_eighteenth_available(self):
        _,v=start({"scanner_live":False})
        self.assertEqual(len(v["filter_selected"]),17)
        self.assertEqual(v["filter_selected"],ALL_FILTERS[:17])
        self.assertEqual(len(ALL_FILTERS),18)
        v["remove_added_filter"](ALL_FILTERS[0])
        self.assertNotIn(ALL_FILTERS[0],v["filter_selected"])
        v["central_filter_settings"]()
        self.assertIn(ALL_FILTERS[0],[x.key for x in v["filter_choice"].options])

    def test_saved_user_filter_selection_is_not_overridden(self):
        saved=["EMA 9/21","PCR"] if "PCR" in ALL_FILTERS else ["EMA 9/21","Max Pain"]
        _,v=start({"scanner_live":False,"scanner_filters":saved,
                   "default_ten_migrated":True})
        self.assertEqual(v["filter_selected"],saved)

    def test_doctor_refresh_state_persists_and_has_timeout(self):
        area=MAIN.split("    def v3_live_building_panel():",1)[1].split("    def settings():",1)[0]
        self.assertIn("busy=v3_diag_busy",area)
        self.assertIn("refreshed=v3_diag_refreshed",area)
        self.assertIn("report=ft.Text(v3_diag_report[0]",area)
        self.assertIn("await asyncio.wait_for(refresh_all_dhan_quotes(),timeout=55)",area)
        self.assertIn("v3_diag_report[0]=report.value",area)
        self.assertIn("REFRESH TIMEOUT",area)

    def test_options_refresh_cannot_sync_rebuild_whole_page_at_completion(self):
        section=MAIN.split("    async def refresh_selected_options():",1)[1].split("    async def option_poll():",1)[0]
        finally_section=section.rsplit("        finally:",1)[1]
        self.assertIn("request_view_refresh(1)",finally_section)
        self.assertNotIn("select(1)",finally_section)

    def test_index_feederror_is_sanitized_and_stage_labeled(self):
        index=MAIN.split("    async def refresh_dhan_index_quotes(force=False):",1)[1].split("    manual_quote_last_attempt=",1)[0]
        self.assertIn('detail=safe_error(exc)',index)
        self.assertIn('display_failures["dhan_index_ltp_batch"]=',index)
        self.assertIn('Dhan index quote route failed',index)
        self.assertIn('check SENSEX IDX_I/51 separately',index)

    def test_filter_doctor_is_stage_specific_and_read_only(self):
        section=MAIN.split("    def filter_five_diagnostic_panel():",1)[1].split(
            "    # Keep the manual Diagnostics",1)[0]
        self.assertIn('"errors_only":errors',section)
        self.assertIn('"provider_requests":0',section)
        self.assertIn('"five_boxes":engines',section)
        self.assertNotIn('dhan_feed.quote,"SENSEX"',section)

    def test_timeframe_isolated_and_no_fake_ltp(self):
        history=MAIN.split("    def shared_history(sym,tf=",1)[1].split("    def ",1)[0]
        self.assertIn('prefs.get("scanner_timeframe","1m")',MAIN)
        self.assertIn('filter_selected[:]=ALL_FILTERS[:17]',MAIN)
        self.assertIn('Restore default 17',MAIN)
        self.assertIn('chart_snapshots.get((sym,tf,provider_generation[0]))',history)
        self.assertIn('scanner_data.get("_scanner_timeframe")==tf',history)
        self.assertNotIn("def sensex_full_diagnostic_panel():",MAIN)
        self.assertIn('"historical_percent":historical_percent',MAIN)
        self.assertIn('"live_market_verified":False',MAIN)

if __name__=="__main__": unittest.main()
