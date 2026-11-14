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


def test_dhan_seven_strike_option_ui_uses_cached_context_only():
    start=SOURCE.index("    def option_chain_preview():")
    end=SOURCE.index("\n    def ",start)
    block=SOURCE[start:end]
    assert "option_chain_display_context(dhan_option_metrics)" in block
    assert 'context.get("available")' in block
    assert 'context["rows"]' in block
    assert "ATM ±3 listed strikes" in block
    assert "UNVERIFIED" in block and "signals WAIT" in block
    assert "live orders OFF" in block
    assert "asyncio.to_thread" not in block
    assert "dhan_feed.option_chain_metrics" not in block
    assert "get_market_data(" not in block


def test_option_window_requires_current_symbol_expiry_and_connected_dhan():
    start=SOURCE.index("    def option_chain_preview():")
    end=SOURCE.index("\n    def ",start)
    block=SOURCE[start:end]
    assert 'prefs.get("source") == "Dhan" and dhan_feed.connected' in block
    assert 'dhan_option_metrics.get("symbol") == chain_symbol.value' in block
    assert 'dhan_option_metrics.get("expiry") == expiry.value' in block
    assert 'context.get("available")' in block


def test_dhan_option_ui_never_falls_back_to_legacy_contract_rows():
    start=SOURCE.index("    def option_chain_preview():")
    end=SOURCE.index("\n    def ",start)
    block=SOURCE[start:end]
    assert 'if prefs.get("source") == "Dhan":' in block
    assert 'No legacy broker CE/PE rows are shown in Dhan-only mode.' in block
    assert block.index('if prefs.get("source") == "Dhan":') < block.index('rows=selected_option_rows();grouped={}')


def test_dhan_option_ui_displays_volume_without_inventing_missing_values():
    start=SOURCE.index("    def option_chain_preview():")
    end=SOURCE.index("\n    def ",start)
    block=SOURCE[start:end]
    assert '["CE Premium","CE OI","CE Vol","Strike","PE Vol","PE OI","PE Premium"]' in block
    assert 'value(item["ce"],"volume")' in block
    assert 'value(item["pe"],"volume")' in block
    assert 'return ("—" if v is None' in block


def test_backend_atm_window_reports_safe_missing_spot_reason():
    backend=Path(__file__).resolve().parents[1].joinpath("backend","server.py").read_text(encoding="utf-8")
    assert 'window_status = "underlying_spot_unavailable"' in backend
    assert 'window_status = "listed_window_unavailable"' in backend
    assert 'window_status = "available"' in backend
    assert '"atm_window_status": window_status' in backend
    assert 'window = listed_atm_window(raw, spot=underlying_spot)' in backend


def test_mobile_option_ui_explains_missing_atm_window_without_signal():
    start=SOURCE.index("    def option_chain_preview():")
    end=SOURCE.index("\n    def ",start)
    block=SOURCE[start:end]
    assert '"underlying_spot_unavailable":"Dhan underlying spot missing"' in block
    assert '"listed_window_unavailable":"Seven valid listed strikes unavailable"' in block
    assert 'dhan_option_metrics.get("atm_window_status")' in block
    assert "signals WAIT" in block


def test_gateway_rejects_inconsistent_option_window_diagnostics():
    feed=Path(__file__).resolve().parents[1].joinpath("src","server_feed.py").read_text(encoding="utf-8")
    assert 'window_status = result.get("atm_window_status")' in feed
    assert 'window_status == "available"' in feed
    assert 'window is not None' in feed
    assert 'Inconsistent Dhan ATM window diagnostic status' in feed


def test_scanner_tab_has_recovery_mode_and_independent_widget_guards():
    start = SOURCE.index("    def scanner():")
    end = SOURCE.index("    def run_scan(e):", start)
    block = SOURCE[start:end]
    assert "return scanner_content()" in block
    assert 'log_error("scanner_page", exc)' in block
    assert 'heading("SCANNER • Recovery Mode")' in block
    assert 'on_click=lambda e:select(3)' in block
    assert 'safe_scanner_widget("Chart",scanner_compact_chart)' in block
    assert 'safe_scanner_widget("Five Engine",lambda:five_engine_summary(' in block
    assert 'safe_scanner_widget("Options",scanner_option_context)' in block
    assert 'log_error("scanner_" + label.lower().replace(" ", "_"), exc)' in block


def test_scanner_fusion_missing_saved_fields_fail_closed():
    start = SOURCE.index("    def fusion_card(symbol,interval,compact=False):")
    end = SOURCE.index("    def ",start + 8)
    block = SOURCE[start:end]
    assert 'scan_shared.get("direction","WAIT")' in block
    assert 'scan_shared.get("basis","Analysis unavailable")' in block
    assert 'scan_shared["direction"]' not in block
    assert 'scan_shared["basis"]' not in block
