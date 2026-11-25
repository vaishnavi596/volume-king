"""Offline regression guards for independent BOT KING watchlist refresh."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchlistRefreshRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_selected_chart_retains_last_good_dhan_history(self):
        body=self.source.split("    async def load_chart():",1)[1].split(
            "    async def visible_chart_poll():",1)[0]
        self.assertIn('prior=chart_snapshots.get((sym,tf,generation)) or {}',body)
        self.assertIn('data=retain_candle_history(data,prior,provider="Dhan")',body)
        self.assertLess(body.index('data=retain_candle_history(data,prior,provider="Dhan")'),
                        body.index('chart_snapshots[(sym,tf,generation)]=data'))

    def test_watchlist_chart_timeframe_tag_survives_retention(self):
        chart=self.source.split("    async def load_chart():",1)[1].split(
            "    async def visible_chart_poll():",1)[0]
        self.assertIn('data=dict(data,_scanner_timeframe=tf)',chart)
        self.assertLess(chart.index('data=retain_candle_history(data,prior,provider="Dhan")'),
                        chart.index('data=dict(data,_scanner_timeframe=tf)'))
        self.assertLess(chart.index('data=dict(data,_scanner_timeframe=tf)'),
                        chart.index('chart_snapshots[(sym,tf,generation)]=data'))

    def test_watchlist_three_minute_warmup_is_bounded_and_foreground_only(self):
        body=self.source.split("    async def watch_three_minute_warmup():",1)[1].split(
            "    page.run_task(watch_three_minute_warmup)",1)[0]
        for guard in ('current[0]!=4','lifecycle_background[0]',
                      'not refresh_hours()','dhan_history_scan_active[0]',
                      'index_one_minute_busy[0]',
                      'dhan_feed.cooldown_remaining("/dhan/intraday")>0'):
            self.assertIn(guard,body)
        self.assertIn("len(watch_three_minute_upstream_times)>=12",body)
        self.assertIn("watch_three_minute_upstream_times.append(attempt_time)",body)
        self.assertIn("watch_three_minute_warm_last_provider[0]<10",body)
        self.assertIn('get_market_data,sym,"1m","2d"',body)
        self.assertIn('chart_snapshots[(sym,"1m",generation)]',body)
        self.assertIn('data=retain_candle_history(data,prior,provider="Dhan")',body)
        self.assertIn("break  # One attempted equity per scheduler tick, never fanout.",body)
        self.assertNotIn('asyncio.gather(',body)
        self.assertNotIn('get_market_data,sym,"3m"',body)

    def test_incomplete_login_watchlist_bootstrap_retries_only_bounded(self):
        source=self.source
        block=source.split("    async def watch_login_candle_bootstrap():",1)[1].split(
            "    page.run_task(watch_login_candle_bootstrap)",1)[0]
        self.assertIn("watch_login_bootstrap_attempts[0]+=1",block)
        self.assertIn("watch_login_bootstrap_attempts[0]>=3",block)
        self.assertIn("watch_login_bootstrap_retry_after[0]=time.monotonic()+180",block)
        self.assertIn("time.monotonic()<watch_login_bootstrap_retry_after[0]",block)
        self.assertIn("if watch_login_bootstrap_generation[0]!=generation:",block)
        self.assertIn("watch_login_bootstrap_attempts[0]=0",block)
        self.assertIn("if completed==total:",block)
        self.assertIn("watch_login_bootstrap_attempts[0]=3",block)
        # Retry must skip cached valid 3m histories and retain last-good 1m.
        self.assertIn('prior=shared_history(sym,"3m")',block)
        self.assertIn('if valid_candle_history(prior.get("bars")):',block)
        self.assertIn('data=retain_candle_history(data,shared_history(sym,"1m"),provider="Dhan")',block)
        # Preserve source, session, pacing, and cache protections. Android
        # background lifecycle alone must no longer interrupt first hydration.
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")',block)
        self.assertIn('await asyncio.sleep(1.5)',block)
        self.assertNotIn('asyncio.gather(',block)
        self.assertIn('watch_bootstrap_stop_requested()',block)
        self.assertNotIn('or not app_active[0]',block)
        self.assertNotIn('lifecycle_background[0]',block)
        self.assertIn('incomplete rows remain WAIT',block)

    def test_background_bootstrap_stop_policy_keeps_process_running_but_not_unknown_inactive(self):
        helper=self.source.split("    def watch_bootstrap_stop_requested():",1)[1].split(
            "    async def watch_login_candle_bootstrap():",1)[0]
        self.assertIn("return not app_active[0] and not lifecycle_background[0]",helper)
        self.assertIn("An OS process freeze still requires a native",helper)


    def test_index_one_minute_yields_to_bounded_watchlist_warmup(self):
        body=self.source.split("    async def dhan_index_candle_poll():",1)[1].split(
            "    page.run_task(dhan_index_candle_poll)",1)[0]
        self.assertIn("not watch_three_minute_warm_busy[0]",body)
        self.assertIn("index_one_minute_busy[0]=True",body)
        self.assertIn("index_one_minute_busy[0]=False",body)

    def test_missing_three_minute_votes_are_not_labeled_live(self):
        body=self.source.split("    def compact_watch_signal(row, available, fresh):",1)[1].split(
            "    def compact_five_engine_watch(",1)[0]
        self.assertIn("3m • WAIT • matching 3m candles / valid votes unavailable",body)
        self.assertIn('row.get("timeframe")=="3m"',body)

    def test_three_minute_signal_recalculates_revised_ohlcv(self):
        # Same timestamp and bar count may still contain a corrected close,
        # high, low or volume; a timestamp-only identity would retain stale votes.
        body=self.source.split("    def watch_three_minute_signal(sym):",1)[1].split(
            "    def refresh_shared_analysis(",1)[0]
        self.assertIn("recent_three=tuple(tuple(row) for row in completed[-4:])",body)
        self.assertIn("identity=context+(recent_three,len(completed)",body)
        self.assertNotIn('completed[-1][0],len(completed),data.get("candle_fetched_at")',body)
        self.assertIn('result=analyze(quality["bars"],selected,"3m")',body)

    def test_python_syntax(self):
        ast.parse(self.source, filename=str(SOURCE))

    def test_quote_poll_uses_connection_aware_interval(self):
        tree = ast.parse(self.source)
        poll = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.AsyncFunctionDef)
                    and node.name == "dhan_quote_poll")
        sleeps = [node for node in ast.walk(poll)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "sleep"]
        self.assertTrue(any(call.args and isinstance(call.args[0], ast.IfExp)
                            and isinstance(call.args[0].body, ast.Constant)
                            and call.args[0].body.value == 10
                            and isinstance(call.args[0].orelse, ast.Constant)
                            and call.args[0].orelse.value == 10 for call in sleeps))

    def test_no_scroll_triggered_quote_requests(self):
        self.assertNotIn("watch_list.on_scroll=", self.source)
        self.assertNotIn("refresh_watch_on_scroll", self.source)

    def test_historical_votes_explicitly_not_live(self):
        self.assertIn("HIST • NOT live", self.source)
        self.assertIn("bgcolor=GREEN,expand=bull", self.source)
        self.assertIn("bgcolor=RED,expand=bear", self.source)

    def test_change_aware_watchlist_refresh(self):
        self.assertIn("if signature==last_visible_signature", self.source)
        self.assertIn("await asyncio.sleep(2)", self.source)
        self.assertIn("if target==4 and current[0]==4 and watch_list.page is not None:", self.source)
        self.assertIn("watch_row_cells[sym]=", self.source)

    def test_oracle_three_minute_cache_revision_wakes_mounted_watch_row(self):
        tick=self.source.split("    async def watch_visible_tick():",1)[1].split(
            "    def watchlist():",1)[0]
        # Assessment can change with unchanged quote/votes. All three gates
        # must observe the identical generation-scoped 3m cache key.
        token='(provider_generation[0],sym,"3m",None)'
        visible=tick.split('signature=(active_watch[0]',1)[1].split('button=watch_refresh_button[0]',1)[0]
        row=tick.split('symbol_signature=(id(cells),',1)[1].split('if last_cell_signatures.get(sym)',1)[0]
        evidence=tick.split('evidence_signature=(',1)[1].split('if last_evidence_signatures.get(sym)',1)[0]
        for gate in (visible,row,evidence):
            self.assertIn(token,gate)
        self.assertEqual(sum(gate.count(token) for gate in (visible,row,evidence)),3)
        self.assertIn('if last_evidence_signatures.get(sym)!=evidence_signature:',tick)
        self.assertIn('oracle_assessment_cache.get(',tick)
        self.assertIn('assessment.content=note(oracle_assessment_notes(sym,"watchlist")[0])',tick)
        # This is a local 2s observation and must not introduce broker fanout.
        self.assertNotIn('dhan_feed.assessment(',tick)
        self.assertNotIn('get_market_data(',tick)

    def test_price_and_filter_cells_have_mounted_identity(self):
        body=self.source.split("    def fill_watch(_=None):",1)[1].split("    search.on_change=fill_watch",1)[0]
        for name in ("price_cell","change_cell","five_cell","assessment_cell",
                     "signal_cell","freshness_cell"):
            self.assertIn(name+"=",body)
        self.assertIn("watch_row_cells[sym]=",body)
        self.assertIn("txt(sym,16,WHITE,True)",body)
        tick=self.source.split("    async def watch_visible_tick():",1)[1].split(
            "    def watchlist():",1)[0]
        self.assertIn("last_cell_signatures[sym]=symbol_signature",tick)
        self.assertIn("if last_cell_signatures.get(sym)==symbol_signature:",tick)
        self.assertIn("if cell.page is not None:cell.update()",tick)
        self.assertIn("if freshness.page is not None:freshness.update()",tick)
        self.assertNotIn("request_view_refresh(4)",tick)
        self.assertNotIn("dhan_feed.batch_quotes",tick)

    def test_manual_button_disabled_flag_tracks_login_and_busy_state(self):
        worker=self.source.split("    async def watch_visible_tick():",1)[1].split(
            "    def watchlist():",1)[0]
        self.assertIn("button=watch_refresh_button[0]",worker)
        self.assertIn("button.disabled=should_disable",worker)
        self.assertIn("if button.page is not None:button.update()",worker)
        builder=self.source.split("    def watchlist():",1)[1].split(
            "    symbol=ft.Dropdown(",1)[0]
        self.assertIn("watch_refresh_button[0]=refresh_btn",builder)
        self.assertIn("watch_status_text.value=",builder)

    def test_watchlist_auto_refresh_is_non_destructive(self):
        flush=self.source.split("    async def flush_view_refresh():",1)[1].split(
            "    def request_view_refresh(i):",1)[0]
        self.assertIn("target==4 and current[0]==4",flush)
        self.assertIn("return",flush)
        manual=self.source.split("    async def refresh_all_dhan_quotes():",1)[1].split(
            "    quote_auto_last_attempt=",1)[0]
        self.assertIn("await refresh_watch_batch()",manual)
        self.assertIn("await refresh_dhan_index_quotes(force=True)",manual)
        self.assertNotIn("quotes.clear()",manual)


if __name__ == "__main__":
    unittest.main()
