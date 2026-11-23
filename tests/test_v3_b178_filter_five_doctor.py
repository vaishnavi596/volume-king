"""B178 phone doctor contract: 17 filters, five independent boxes, no SENSEX-only probe."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"src"/"main.py").read_text(encoding="utf-8")

class FilterFiveDoctorContract(unittest.TestCase):
    def test_main_app_compiles_and_old_sensex_tool_is_removed(self):
        ast.parse(APP)
        self.assertNotIn("def sensex_full_diagnostic_panel():",APP)
        self.assertNotIn("content.append(sensex_full_diagnostic_panel())",APP)
        self.assertNotIn("SENSEX FULL DIAG (read-only)",APP)

    def test_main_doctor_contains_all_filters_and_five_box_diagnosis(self):
        start=APP.index("    def filter_five_diagnostic_panel():")
        end=APP.index("    # Keep the manual Diagnostics gate",start)
        panel=APP[start:end]
        self.assertIn('names=list(filter_selected)',panel)
        self.assertIn('complete_filter_rows(result,names,filter_modes)',panel)
        self.assertIn('enrich_context_filter_rows(symbol,',panel)
        self.assertIn('read_five_engine_context(symbol,tf)',panel)
        for name in ('technical','candle','news','futures','options'):
            self.assertIn('"'+name+'"',panel)
        self.assertIn('"errors_only":errors',panel)
        self.assertIn('"filter_results":filter_rows',panel)
        self.assertIn('"five_boxes":engines',panel)
        self.assertIn('"stage_context":diagnostic_context',panel)
        self.assertIn('"cache_to_display_trace":pipeline_trace',panel)
        for stage in ("CACHE_INPUT", "TIMEFRAME_AND_SOURCE", "CANDLE_VALIDATION",
                      "FILTER_ANALYSIS", "FIVE_ENGINE_ADAPTER", "DASHBOARD_UI_INPUT"):
            self.assertIn(stage,panel)
        self.assertIn('chart_snapshots.get((symbol,tf,generation))',panel)
        self.assertIn('scanner_cache_exact_match',panel)
        self.assertIn('verified_display_boxes',panel)
        self.assertIn('Flutter pixels not measured',panel)
        for blocker in ("CANDLE_HISTORY_MISSING", "TECHNICAL_VOTES_OR_FRESHNESS_UNVERIFIED",
                        "INDEPENDENT_CANDLE_EVIDENCE_UNVERIFIED",
                        "HEADLINES_PRESENT_DIRECTION_UNVERIFIED",
                        "VERIFIED_FUTURES_FLOW_OR_MAPPING_MISSING",
                        "OPTION_EXPIRY_CONTEXT_MISSING",
                        "PCR_OI_PRESENT_NOT_VERIFIED_TRADE_DIRECTION"):
            self.assertIn(blocker,panel)
        self.assertIn('"cached_news_count"',panel)
        self.assertIn('"option_pcr_present"',panel)
        for expected in ('"freshness_gate":freshness_issue','"raw_evidence_reason"',
                         '"evidence_age_seconds":evidence_age',
                         '"raw_verified":raw_verified','"raw_source":str(raw_source)',
                         '"historical_candle_balance_status"',
                         '"index_route_diagnostic"', '"cooldown_seconds"',
                         '"last_attempt_same_generation"', '"worker_busy"'):
            self.assertIn(expected,panel)
        self.assertIn('raw_snapshot=(five_engine_snapshots.get(symbol)',panel)
        self.assertIn('if tf in ("1m","3m","5m") and prefs.get("source")=="Dhan"',panel)
        self.assertIn('"NO_EXACT_TIMEFRAME_ENGINE_PUBLISHER"',panel)
        self.assertIn('now_for_evidence=time.time()',panel)
        for token in ('"failure_code":index_failure_code[0]',
                      '"last_eight_candle_ohlc_diagnostics"',
                      '"candle_balance_min_directional_bodies"',
                      '"DOJI_DOMINATED_LT_FIVE_DIRECTIONAL"',
                      '"MALFORMED_LAST_EIGHT"'):
            self.assertIn(token,panel)
        for token in ('"NETWORK_OR_TIMEOUT"', '"INDEX_BATCH_SCHEMA_REJECTED"',
                      '"GATEWAY_HTTP_429"',
                      'index_failure_code[0]="NONE_ALL_THREE_QUOTES_PRESENT"'):
            self.assertIn(token,APP)
        self.assertIn('"history_shape_valid"',panel)
        self.assertIn('"analysis_uses_exact_timeframe"',panel)
        self.assertIn('"CONTEXT_ONLY" if context_ready else "WAIT"',panel)
        self.assertIn('"OI_CONTEXT_NO_DIRECTIONAL_VOTE"',panel)
        self.assertIn('"context_only":sum(',panel)
        self.assertIn('historical_vote_agreement(history,tf)',panel)
        self.assertIn('completed_timeframe_candle_balance(',panel)
        self.assertIn('"timeframe":tf',panel)
        self.assertNotIn('saved=watch_signal_cache.get(symbol)',panel)
        self.assertIn('"provider_requests":0',panel)
        self.assertIn('chart_snapshots.get((symbol,tf,generation))',panel)
        self.assertNotIn('stock_histories.get((symbol,tf,generation))',panel)
        self.assertIn('"error_field":',panel)
        self.assertIn('"HIST_ONLY"',panel)
        self.assertIn('"bullish_percent":bull if ready else None',panel)
        self.assertIn('"bearish_percent":bear if ready else None',panel)
        self.assertIn("FILTER + FIVE BOX DIAG (read-only)",panel)

    def test_master_diagnostic_reports_all_segments_without_provider_requests(self):
        start=APP.index("    def master_diagnostic_panel():")
        end=APP.index("    def v3_live_building_panel():",start)
        panel=APP[start:end]
        for segment in ("ADAPTER_CONNECTION_MAP","PAPER_ADAPTER_AUDIT","GATEWAY_REFRESH","WATCHLIST_54_70","CANDLE_TIMEFRAMES",
                        "SCANNER_17","SUPER_FIVE_ENGINES","DASHBOARD_INDICES",
                        "OPTIONS_NEWS_FUTURES","CHART_UI","ERRORS_COORDINATION",
                        "BACKGROUND_LIFECYCLE"):
            self.assertIn('"'+segment+'"',panel)
        for expected in ('"V3_MASTER_ALL_SEGMENTS_DOCTOR"',
                         '"segments":sections if chosen=="ALL"',
                         '"provider_requests":0,"orders_sent":0',
                         '"global_equity_limit":70',
                         '"visible_tick_seconds":2',
                         '"warmup_floor_seconds":30',
                         '"watchlist_default":"3m"',
                         '"dashboard_index_default":"1m"',
                         '"sixth_placeholder":"INERT_NOT_SCORED"',
                         '"physical_flutter_paint_measured":False',
                         'MASTER DIAG • ALL SEGMENTS (read-only)'):
            self.assertIn(expected,panel)
        for source_code in ('ANDROID_LIFECYCLE_PAUSES_PYTHON_WORK',
                            'BACKGROUND_CONTINUITY_NOT_PROVEN',
                            'INDEPENDENT_FIVE_ENGINE_EVIDENCE_NOT_READY',
                            'WATCHLIST_CAP_OR_DUPLICATE_POLICY',
                            '3M_WARMUP_RATE_BUDGET_FULL',
                            '"root_cause_and_solution":remedies',
                            '"code_diagnostic_limit"',
                            '"foreground_service_implemented":False',
                            '"android_workmanager_implemented":False',
                            '"force_stop_continuity_supported":False',
                            'src/main.py:lifecycle_changed'):
            self.assertIn(source_code,panel)
        for disallowed in ('dhan_feed._call(', 'dhan_feed.history(',
                           'get_market_data(', 'dhan_feed.quote(',
                           'refresh_all_dhan_quotes('):
            self.assertNotIn(disallowed,panel)
        self.assertIn('master_diagnostic_panel(),',APP[end:APP.index("    def settings():",end)])
        for field in ('"index_last_result_state"', '"index_last_result_generation_matches"',
                      '"index_result_age_seconds"', '"ui_signal_reuse"',
                      '"last_eight_ohlc_body_counts"', '"volume_scale_review_required"',
                      '"rsi_extreme_review_required"'):
            self.assertIn(field,panel)
        for derived_marker in ('"selected_equities_with_valid_effective_3m"',
                               '"valid_locally_derived_3m"',
                               'shared_history(watch_sym,"3m")',
                               '"Materialized cache entries exclude on-demand completed 1m-to-3m histories"'):
            self.assertIn(derived_marker,panel)
        for extra in ('"local_inspection_elapsed_ms"',
                      '"per_index_cache_and_context":index_context',
                      '"quote_cache_age_seconds"',
                      '"news_headline_count"',
                      '"index_failure_next_stage"',
                      '"other_indices_option_context_not_inferred":True'):
            self.assertIn(extra,panel)
        self.assertIn('clean=canonical_filter_selection(previous)',APP)
        self.assertIn('target[:]=canonical_filter_selection(values)',APP)
        self.assertIn('if name=="Dhan Max Pain"',APP)
        self.assertIn('data["max_pain"]',APP)
        engine=(ROOT/"src"/"five_engine.py").read_text(encoding="utf-8")
        catalog=(ROOT/"src"/"scanner_engine.py").read_text(encoding="utf-8")
        self.assertIn('"Dhan Max Pain"',engine)
        self.assertIn('"Dhan Max Pain"',catalog)
        self.assertNotIn('"Max Pain"',engine)
        # Standalone Max Pain must be absent from the active registry;
        # the literal stays ONLY to migrate old saved settings one-way.
        from scanner_engine import ALL_FILTERS, canonical_filter_selection
        self.assertNotIn("Max Pain",ALL_FILTERS)
        self.assertEqual(ALL_FILTERS.count("Dhan Max Pain"),1)
        self.assertEqual(canonical_filter_selection(
            ["Max Pain","Dhan Max Pain","Max Pain"]),["Dhan Max Pain"])
        self.assertIn('name == "Max Pain"',catalog)
        for removed_label in ('OI / PCR / Max Pain:',
                              'OI / PCR / MAX PAIN • INFORMATION ONLY',
                              'OI Profile and Max Pain can be selected',
                              ' • Max Pain '):
            self.assertNotIn(removed_label,APP)

        self.assertIn('watch_cell_age_flags(sym,now_epoch=None,precomputed_signal=None)',APP)
        tick=APP[APP.index('    async def watch_visible_tick():'):APP.index('    def watchlist():')]
        self.assertEqual(tick.count('watch_cell_age_flags(sym,precomputed_signal=tick_signals[sym])'),3)
        self.assertIn('"mounted_3m_signal_tick_performance":dict(watch_3m_tick_profile)',APP)
        for audit_field in ('"paper_bot_engine":"MANUAL_MARK_ONLY"',
                            '"legacy_chart_paper_handler_mounted":False',
                            '"option_premium_chart_adapter":"LEGACY_ANGEL_ONLY_UNAVAILABLE_FOR_DHAN"',
                            '"live_order_buttons_enabled":False',
                            '"chart_local_filter_profile":dict(chart_filter_profile)',
                            '"chart_exact_timeframe_cache_present"',
                            '"chart_uses_shared_cached_history_without_provider_on_open":True',
                            'content.append(chart_filter_evidence())'):
            self.assertIn(audit_field,APP)
        self.assertIn('def chart_filter_evidence():',APP)
        for readiness_marker in ('"ADAPTER_CONNECTION_MAP"',
                                 '"DHAN_TRANSPORT":adapter_row(',
                                 '"ORACLE_CLONE_GATEWAY":adapter_row(',
                                 '"INDEX_BATCH":adapter_row(',
                                 '"WATCHLIST_3M":adapter_row(',
                                 '"CHART_LAST_TAB":adapter_row(',
                                 '"PAPER_BOT":adapter_row(',
                                 '"LIVE_ORDER":adapter_row(',
                                 '"PERMANENTLY_LOCKED"',
                                 '"adapter_count":len(adapter_map)',
                                 '"provider_requests":0,"orders_sent":0'):
            self.assertIn(readiness_marker,APP)

        self.assertIn('initial_trading_mode="Paper" if prefs.get("mode")=="Paper" else "Live (locked)"',APP)
        self.assertIn('ft.dropdown.Option("Live (locked)","Live trading • permanently disabled")',APP)
        self.assertNotIn('for x in ["Paper","Manual","Semi-Auto","Auto"]',APP)
        self.assertIn('if key=="mode" and value in ("Manual","Semi-Auto","Auto","Live (locked)"):',APP)
        self.assertIn('if prefs.get("source")!="Dhan":',APP)
        self.assertIn('prefs["source"]="Dhan"',APP)
        self.assertNotIn('if prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan")',APP)

        for paper_marker in ('def paper_dhan_reference():',
                             'def paper_mark_pnl_preview():',
                             '"paper_simulated_order_events":sum(',
                             '"paper_pnl_calculation":"MANUAL_MARK_ONLY_ZERO_FEES_PREVIEW"',
                             '"paper_dhan_market_reference_only":True',
                             'PAPER ORDER & P&L STATUS',
                             'LIVE orders permanently OFF'):
            self.assertIn(paper_marker,APP)

        self.assertIn('chart_snapshots[chart_key]=dict(existing,',APP)

        self.assertIn('tick_started=time.perf_counter()',APP)
        self.assertIn('watch_3m_tick_profile["last_symbols"]=len(visible)',APP)
        self.assertIn('"index_result_state":index_last_result_state[0]',APP)
        self.assertIn('"index_same_generation":index_last_result_generation[0]==generation',APP)
        self.assertIn('"last_eight_distinct_timestamps"',APP)
        self.assertIn('"last_candle_age_seconds"',APP)

    def test_panel_is_embedded_in_existing_main_error_doctor(self):
        start=APP.index("    def v3_live_building_panel():")
        end=APP.index("    def settings():",start)
        self.assertIn("filter_five_diagnostic_panel(),",APP[start:end])
        self.assertIn("content.append(v3_live_building_panel())",APP)

if __name__=="__main__":
    unittest.main()
