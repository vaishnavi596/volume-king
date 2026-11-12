"""Regression guard: failed/partial Dhan batch must not blank last valid quotes."""
from pathlib import Path


def test_dhan_login_batch_preserves_last_valid_quotes():
    source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
    begin = source.index("                    # Verify watchlist batch independently of the login check.")
    end = source.index("                    if market_status.startswith", begin)
    batch = source[begin:end]
    assert "quotes[ticker]=dict(snapshot" in batch
    assert "Partial Dhan batch:" in batch
    assert "dhan_batch_issue[0]=safe_error(exc)" in batch
    assert "quotes.pop(ticker,None)" not in batch
    assert "A failed refresh must not erase the last valid Dhan quote" in batch
