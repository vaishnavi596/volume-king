"""Protect fast first-visible Dhan candle loading without changing rate limits."""
from pathlib import Path


def test_dashboard_symbols_precede_remaining_watchlist_on_cold_start():
    source=(Path(__file__).resolve().parents[1]/'src'/'main.py').read_text(encoding='utf-8')
    queue=source.split('dashboard_priority=[prefs.get("dashboard_analysis_slot_"',1)[1]
    assert 'priority=[scan_symbol.value or "NIFTY"]+dashboard_priority+' in queue
    assert 'symbols=list(dict.fromkeys(' in queue
    assert 'symbols=[sym for sym in symbols if sym!="NIFTY"]' in queue
    assert 'await asyncio.sleep(1.5)' in queue
