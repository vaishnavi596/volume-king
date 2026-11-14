"""Batch 4 UI uses cached five-engine evidence; never fetches per engine."""
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1].joinpath("src","main.py").read_text(encoding="utf-8")


def test_five_engine_summary_is_cache_only():
    start=SOURCE.index("    def five_engine_summary(symbol):")
    end=SOURCE.index("    def super_five_card():",start)
    block=SOURCE[start:end]
    assert "five_engine_snapshots.get(symbol)" in block
    assert "evidence.display()" in block
    assert 'combined["coverage"]' in block
    assert "get_market_data(" not in block
    assert "await " not in block
    assert "requests." not in block


def test_five_engine_summary_present_on_both_surfaces():
    assert 'five_engine_summary(row["symbol"])' in SOURCE
    assert 'five_engine_summary(scan_symbol.value or "NIFTY")' in SOURCE
    assert 'five_engine_snapshots[sym]=scanner_snapshot(' in SOURCE
