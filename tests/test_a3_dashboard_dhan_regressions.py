"""A3: user-targeted Dashboard 0/3 removal, native Dhan mini charts, saved 10 movable slots."""
import ast
from pathlib import Path
from test_audit import start

ROOT=Path(__file__).resolve().parents[1]/"src"
MAIN=ROOT/"main.py"


def test_dashboard_only_removes_old_three_input_fusion_card():
    source=MAIN.read_text(encoding="utf-8")
    ast.parse(source)
    dashboard=source.split("    def dashboard():",1)[1].split("    search=ft.TextField(",1)[0]
    assert "fusion_card(" not in dashboard
    assert "dashboard_index_analysis()" in dashboard
    assert "super_five_card()" in dashboard
    assert "CANDLE ANALYSIS" in dashboard
    assert "OPTIONS DATA" in dashboard


def test_selected_dashboard_slots_reuse_dhan_native_candles_without_network():
    source=MAIN.read_text(encoding="utf-8")
    chart=source.split("    def dashboard_mini_candles(",1)[1].split("    def help_status(",1)[0]
    assert "clean_bars(data.get(\"bars\") or [])[-24:]" in chart
    assert 'data.get("source")!="Dhan"' in chart
    assert "ft.Stack(items" in chart
    assert "asyncio.to_thread" not in chart
    assert "get_market_data(" not in chart
    section=source.split("    def dashboard_index_analysis():",1)[1].split("    def dashboard_market_indices():",1)[0]
    assert "rows.append(dashboard_mini_candles(sym,candle_data))" in section
    assert 'shared_history(sym,"1m")' in section


def test_preserve_fifteen_movable_saved_slots():
    source=MAIN.read_text(encoding="utf-8")
    assert "MAX_ACTIVE_FILTERS=15" in source
    assert "DEFAULT_FILTERS[:]" in source
    assert "[:MAX_ACTIVE_FILTERS]" in source
    assert "len(filter_selected)>=MAX_ACTIVE_FILTERS" in source
    assert 'prefs["scanner_filters"]=filter_selected[:]' in source
    assert "15-slot list" in source


def test_production_broker_and_help_are_dhan_only():
    source=MAIN.read_text(encoding="utf-8")
    assert 'broker_names=["Dhan"]' in source
    assert 'options=[ft.dropdown.Option("Dhan")]' in source
    assert 'note(\'Dhan-only read-only charts/scanner and option metrics.' in source
    assert 'Historical option candles unavailable • no simulated chart; Dhan data only.' in source
    assert 'Dhan server ' in source


def test_dhan_ui_still_available_after_dashboard_caption_removal():
    _,views=start({"scanner_live":False,"source":"Dhan"})
    # No hidden derivative computation was injected by rendering a Dashboard.
    dashboard=views["dashboard"]()
    assert dashboard
    assert views["prefs"]["source"]=="Dhan"

import unittest


class A3RegressionTests(unittest.TestCase):
    def test_only_old_fusion_dashboard_card_removed(self):
        test_dashboard_only_removes_old_three_input_fusion_card()

    def test_native_dashboard_candles_use_existing_dhan_history(self):
        test_selected_dashboard_slots_reuse_dhan_native_candles_without_network()

    def test_fifteen_movable_saved_filter_slots(self):
        test_preserve_fifteen_movable_saved_slots()

    def test_user_visible_provider_is_dhan_only(self):
        test_production_broker_and_help_are_dhan_only()

    def test_dashboard_still_renders(self):
        test_dhan_ui_still_available_after_dashboard_caption_removal()

    def test_five_engine_chips_are_safe_and_consistent(self):
        source=MAIN.read_text(encoding="utf-8")
        area=source.split("    def five_engine_chips(sym):",1)[1].split("    def super_five_card():",1)[0]
        self.assertIn('snapshot_for_display(',area)
        self.assertIn('raw.get("source")=="Dhan"',area)
        self.assertIn('label=short+" WAIT"',area)
        self.assertIn('historical=True',area)
        self.assertNotIn('get_market_data(',area)
        self.assertNotIn('asyncio.to_thread',area)
        for site in ('five_engine_chips(sym)', 'five_engine_chips(index_name)',
                     'five_engine_chips(row["symbol"])'):
            self.assertIn(site,source)
        _,views=start({"scanner_live":False,"source":"Dhan"})
        chips=views["five_engine_chips"]("NIFTY")
        labels=[c.content.value for c in chips.controls]
        self.assertEqual(labels,["T WAIT","C WAIT","N WAIT","F WAIT","O WAIT"])
