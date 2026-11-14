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


def test_provider_generation_invalidates_five_engine_cache():
    # Login, restore/reset and provider selection all rotate the data generation.
    assert SOURCE.count("provider_generation[0]+=1;five_engine_snapshots.clear()")==3
    assert "snapshot_for_display(five_engine_snapshots.get(symbol),now=time.time())" in SOURCE


def test_five_engine_ui_requires_current_dhan_connection():
    for method in ("def five_engine_summary(symbol):","def compact_five_engine_watch(symbol):"):
        block=SOURCE.split(method,1)[1].split("\\n    def ",1)[0]
        assert 'prefs.get("source")!="Dhan" or not dhan_feed.connected' in block
        assert "WAIT" in block


def test_unavailable_five_engine_evidence_explains_wait():
    assert 'else " WAIT ("+str(result["reason"])+")"' in SOURCE
    assert 'str(snapshot["engines"][0].display()["reason"])' in SOURCE


def test_options_display_reuses_existing_cached_component_without_extra_poll():
    assert 'option_from_component(option_component(symbol, "5m"))' in SOURCE
    assert 'pieces[-1]="Options "+option_context.display()["state"]' in SOURCE


def test_options_reason_visible_even_without_scanner_snapshot():
    assert 'if not snapshot:\n            # The cached option context' in SOURCE
    assert 'option_context.reason+")")' in SOURCE


def test_uncertain_rss_headlines_use_real_word_boundaries():
    # The previous regex contained literal backspace characters, not \\b boundaries.
    assert 'r"\\b(not|denies|denied|rumour|rumor|may|could)\\b"' in SOURCE
    assert '\\x08' not in SOURCE


def test_legacy_three_source_fusion_does_not_promote_rss_sentiment_to_vote():
    start = SOURCE.index("    def combine_analysis(symbol,interval,candle,local_news,global_news):")
    end = SOURCE.index("    async def load_combined(", start)
    block = SOURCE[start:end]
    assert "news_bias=None" in block
    assert 'news_bias={"POSITIVE":"BULLISH","NEGATIVE":"BEARISH"}' not in block
    assert "overall=votes[0] if complete and len(set(votes))==1 else \"WAIT\"" in block


def test_legacy_news_context_uses_shared_dedup_and_provenance_gate():
    assert "deduplicate_news_context" in SOURCE
    start = SOURCE.index("    def combine_analysis(symbol,interval,candle,local_news,global_news):")
    end = SOURCE.index("    async def load_combined(", start)
    block = SOURCE[start:end]
    assert "deduplicate_news_context(tagged,symbol=symbol,now=now,max_age_seconds=86400)" in block
    assert '"publisher":x.get("source")' in block
    assert "news_bias=None" in block
