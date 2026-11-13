"""Dhan index cards must not imply that the 51-equity snapshot contains indexes."""
from pathlib import Path


def test_index_dashboard_reports_missing_index_quote():
    source = (Path(__file__).resolve().parents[1] / 'src' / 'main.py').read_text(encoding='utf-8')
    panel = source.split('    def dashboard_index_analysis():', 1)[1].split('    def dashboard():', 1)[0]
    assert 'sym in ("NIFTY","BANKNIFTY","SENSEX")' in panel
    assert 'NIFTY mapping exists; individual Dhan index LTP not available yet' in panel
    assert 'BANK NIFTY / SENSEX instrument mapping not verified' in panel
    assert 'snapshot["price"]<=0' in panel
    assert 'rows.append(note(rows_note))' in panel
