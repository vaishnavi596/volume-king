"""Regression: scheduled Dhan poll shares recent scanner snapshot; manual refresh is fresh."""
from pathlib import Path


def test_poll_reuses_recent_same_generation_dhan_snapshot():
    source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
    start=source.index("    async def refresh_watch_batch(reuse_recent=False):")
    end=source.index("    async def dhan_quote_poll():",start)
    body=source[start:end]
    assert 'reuse_recent and dhan_batch_cache["generation"]==generation' in body
    assert 'time.monotonic()-dhan_batch_cache["updated"]<30' in body
    assert 'else await asyncio.to_thread(dhan_feed.batch_quotes)' in body
    poll=source[end:source.index("    def watchlist():",end)]
    assert 'await refresh_watch_batch(reuse_recent=True)' in poll
    assert 'on_click=lambda e:page.run_task(refresh_watch_batch)' in source
