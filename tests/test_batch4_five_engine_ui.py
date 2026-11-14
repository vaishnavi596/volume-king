"""Batch 4 UI uses cached five-engine evidence; never fetches per engine."""
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1].joinpath("src","main.py").read_text(encoding="utf-8")


def test_five_engine_summary_is_cache_only():
    start=SOURCE.index("    def five_engine_summary(symbol):")
    end=SOURCE.index("    def super_five_card():",start)
    block=SOURCE[start:end]
    assert "snapshot_for_display(five_engine_snapshots.get(symbol),now=time.time())" in block
    assert "evidence.display()" in block
    assert 'combined["coverage"]' in block
    assert "get_market_data(" not in block
    assert "await " not in block
    assert "requests." not in block


def test_five_engine_summary_present_on_both_surfaces():
    assert 'five_engine_summary(row["symbol"])' in SOURCE
    assert 'five_engine_summary(scan_symbol.value or "NIFTY")' in SOURCE
    assert 'five_engine_snapshots[sym]=scanner_snapshot(' in SOURCE


def test_compact_watchlist_reads_only_existing_evidence():
    start=SOURCE.index("    def compact_five_engine_watch(symbol):")
    end=SOURCE.index("    def fill_watch(",start)
    block=SOURCE[start:end]
    assert "five_engine_snapshots.get(symbol)" in block
    assert 'snapshot["combined"]["coverage"]' in block
    assert "get_market_data(" not in block
    assert "dhan_feed." not in block
    assert "await " not in block
    assert "compact_five_engine_watch(sym)" in SOURCE


def test_scanner_five_engine_requires_analysis_and_candle_provenance():
    assert 'analyzed.get("source")=="Dhan"' in SOURCE
    assert '(data or {}).get("source")=="Dhan"' in SOURCE
    assert 'analyzed.get("live_verified") is True' in SOURCE
    assert '(data or {}).get("live_verified") is True' in SOURCE
    assert 'analyzed.get("historical") is False' in SOURCE
    assert '(data or {}).get("historical") is False' in SOURCE
    assert 'freshness="verified_live" if verified else "unverified"' in SOURCE
