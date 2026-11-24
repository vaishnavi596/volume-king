"""Dhan index cards must not imply that the 51-equity snapshot contains indexes."""
from pathlib import Path


def test_index_dashboard_reports_missing_index_quote():
    source = (Path(__file__).resolve().parents[1] / 'src' / 'main.py').read_text(encoding='utf-8')
    panel = source.split('    def dashboard_index_analysis():', 1)[1].split('    def dashboard():', 1)[0]
    assert 'sym in ("NIFTY","BANKNIFTY","SENSEX")' in panel
    assert 'Index Dhan LTP unavailable' in panel
    assert 'instrument mapping not verified' not in panel
    assert 'snapshot["price"]<=0' in panel
    assert 'rows.append(note(rows_note))' in panel


def test_watchlist_index_cards_distinguish_cached_quotes():
    source = (Path(__file__).resolve().parents[1] / 'src' / 'main.py').read_text(encoding='utf-8')
    panel = source.split('    def watchlist():', 1)[1].split('    symbol=ft.Dropdown(', 1)[0]
    assert 'Dhan LTP • cached/unverified' in panel
    assert 'Dhan LTP • exchange time unverified' in panel
    assert 'Dhan LTP unavailable' in panel
