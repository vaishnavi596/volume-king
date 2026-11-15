"""A2 safety regressions: native chart recovery, filter slots, and option refresh.

These are structural checks for the mobile UI. They do not claim to verify
broker data or a real Android WebView, which require device/integration tests.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


def main_source():
    source = SOURCE.read_text(encoding="utf-8")
    ast.parse(source)  # Fail fast on an invalid APK entrypoint.
    return source


def test_chart_recovers_to_native_dhan_candles():
    source = main_source()
    assert "tv_native_fallback=[False]" in source
    assert "tv_mount_retries[0]>=2" in source
    assert "tv_native_fallback[0]=True" in source
    assert 'chart_provider[0]=="TradingView Lightweight" and not tv_native_fallback[0]' in source
    assert 'bars=clean_bars(hist.get("bars") or [])[-35:]' in source
    assert 'Retry Lightweight chart' in source


def test_filter_slots_are_saved_with_explicit_limit():
    source = main_source()
    assert 'filter_selected=list(dict.fromkeys' in source
    assert '[:10]' in source
    assert 'elif len(filter_selected)>=10:' in source
    assert 'prefs["scanner_filters"]=filter_selected[:]' in source
    assert 'prefs["scanner_added_filters"]=added_filters[:]' in source
    assert 'ft.OutlinedButton("Add",on_click=lambda e,n=name:add_filter_slot(n)' in source
    assert 'filter_choice.value=None' in source


def test_dhan_option_refresh_visible_and_read_only():
    source = main_source()
    assert 'Refresh Dhan Option Chain' in source
    assert '# A changed symbol/expiry must fetch its own Dhan read-only snapshot.' in source
    assert 'page.run_task(refresh_selected_options)' in source
    assert 'dhan_feed.option_expiries,sym' in source
    assert 'dhan_feed.option_chain_metrics,sym,chosen' in source
    assert 'option_snapshots.pop(sym,None)' in source  # Unverified metrics never vote.
    assert 'No legacy broker CE/PE rows are shown in Dhan-only mode.' in source


def test_dhan_only_options_hide_legacy_angel_one_prompt():
    source = main_source()
    panel = source.split("    def option_chart_panel():", 1)[1].split("    def quote_caption(sym):", 1)[0]
    assert "Dhan CE/PE premium history" in panel
    assert "Refresh Dhan Option Chain" in panel
    assert "Angel One in Settings" not in panel
    assert "angel_feed.option_history" not in panel
    assert "no simulated chart, no Angel One fallback" in panel
