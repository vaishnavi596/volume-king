"""Regression guard: failed/partial Dhan batch must not blank last valid quotes."""
from pathlib import Path


def test_dhan_login_batch_preserves_last_valid_quotes():
    source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
    begin = source.index("                    # Verify watchlist batch independently of the login check.")
    end = source.index("                    if market_status.startswith", begin)
    batch = source[begin:end]
    assert "quotes[ticker]=dict(snapshot" in batch
    assert "previous.get('bars',[]) if previous.get('source')=='Dhan' else []" in batch
    assert "math.isfinite(snapshot['price']) and snapshot['price']>0" in batch
    assert "Partial Dhan batch:" in batch
    assert "received=sum(1 for ticker in all_watch_symbols()" in batch
    assert "math.isfinite(item['price']) and item['price']>0" in batch
    assert "dhan_batch_issue[0]=safe_error(exc)" in batch
    assert "quotes.pop(ticker,None)" not in batch
    assert "A failed refresh must not erase the last valid Dhan quote" in batch

def test_closed_session_retry_not_blocked_by_old_saved_equity_prices():
    text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
    poll=text.split("    async def dhan_quote_poll():",1)[1].split("    # Compact countdown updates independently",1)[0]
    login=text.split("    async def connect_angel():",1)[1].split('    def provider_changed(',1)[0] if '    def provider_changed(' in text.split("    async def connect_angel():",1)[1] else text.split("    async def connect_angel():",1)[1].split('    def clear_broker_credentials(',1)[0]
    assert "watch_batch_success_generation[0]!=provider_generation[0]" in poll
    assert "closed_equity_bootstrap_generation[0]!=provider_generation[0]" in poll
    assert 'cooldown_remaining("/v2/snapshot")' in poll
    assert 'time.monotonic()-max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60' in poll
    assert "watch_batch_success_generation[0]=provider_generation[0]" in login
    assert "regular_hours()" in login
    assert "page.run_task(refresh_watch_batch)" in login
