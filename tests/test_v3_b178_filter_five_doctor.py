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
        self.assertIn('snapshot_for_display(five_engine_snapshots.get(symbol)',panel)
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
        self.assertIn('raw_snapshot=five_engine_snapshots.get(symbol)',panel)
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
        self.assertIn('historical_candle_balance(bars)',panel)
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
        for segment in ("GATEWAY_REFRESH","WATCHLIST_54_70","CANDLE_TIMEFRAMES",
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
        self.assertIn('"Dhan Max Pain" if name=="Max Pain" else name',APP)
        self.assertIn('if name=="Dhan Max Pain"',APP)
        self.assertIn('data["max_pain"]',APP)
        self.assertIn('watch_cell_age_flags(sym,now_epoch=None,precomputed_signal=None)',APP)
        tick=APP[APP.index('    async def watch_visible_tick():'):APP.index('    def watchlist():')]
        self.assertEqual(tick.count('watch_cell_age_flags(sym,precomputed_signal=tick_signals[sym])'),3)
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
