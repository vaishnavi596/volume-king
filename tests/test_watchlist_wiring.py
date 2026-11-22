"""Offline watchlist wiring regression checks (no broker or UI session required)."""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchlistWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.functions = {
            node.name: node
            for node in ast.walk(cls.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_five_independent_persisted_lists(self):
        self.assertIn('for i in range(1,6)', self.source)
        self.assertIn('prefs["watchlist_"+str(i)]', self.source)
        self.assertIn('for i,group in enumerate(watch_groups,1)', self.source)

    def test_add_captures_target_list_before_async_work(self):
        add = ast.get_source_segment(self.source, self.functions["add_watch"])
        validate = self.functions["validate_and_add"]
        self.assertEqual([arg.arg for arg in validate.args.args], ["sym", "target_list"])
        self.assertIn("target_list=active_watch[0]", add)
        self.assertIn("page.run_task(validate_and_add,sym,target_list)", add)
        body = ast.get_source_segment(self.source, validate)
        self.assertIn("watch_groups[target_list]", body)
        self.assertIn("if active_watch[0]==target_list:", body)
        self.assertIn("if sym not in watch_symbols:", body)

    def test_custom_dhan_symbols_require_registry_not_yahoo_quote(self):
        body = ast.get_source_segment(self.source, self.functions["validate_and_add"])
        self.assertIn("verified_equity_symbol,sym",body)
        self.assertIn('if prefs.get("source")=="Dhan"',body)
        self.assertIn("Dhan quote pending",body)
        feed = (SOURCE.parent / "server_feed.py").read_text(encoding="utf-8")
        self.assertIn("def verified_equity_symbol(self, symbol):",feed)
        self.assertIn("/v2/instruments/search?q=",feed)

    def test_no_duplicate_symbol_across_five_watchlists(self):
        owner = ast.get_source_segment(self.source, self.functions["watch_symbol_owner"])
        self.assertIn("enumerate(watch_groups)",owner)
        self.assertIn("sym in group",owner)
        validate = ast.get_source_segment(self.source, self.functions["validate_and_add"])
        add = ast.get_source_segment(self.source, self.functions["add_watch"])
        self.assertIn("owner=watch_symbol_owner(sym)",validate)
        self.assertIn("owner!=target_list",validate)
        self.assertIn("watch_symbol_owner(sym) is not None",add)
        self.assertIn("Remove it there before adding",validate)
        self.assertIn("Remove it there before adding",add)

    def test_remove_is_list_scoped_and_persisted(self):
        remove = ast.get_source_segment(self.source, self.functions["remove_stock"])
        self.assertIn("watch_groups[active_watch[0]]", remove)
        self.assertIn("group.remove(sym)", remove)
        self.assertIn("store_watch()", remove)

    def test_search_filter_and_chart_click_wired(self):
        self.assertIn("search.on_change=fill_watch", self.source)
        self.assertIn("watch_filter[0]!=signal_direction", self.source)
        self.assertIn("on_click=lambda e,v=sym:open_stock(v)", self.source)
        self.assertIn("on_click=lambda e,v=sym:remove_stock(v)", self.source)

    def test_dhan_client_allows_only_verified_watchlist_symbols(self):
        feed = (SOURCE.parent / "server_feed.py").read_text(encoding="utf-8")
        self.assertIn("DHAN_VERIFIED_EQUITY_SYMBOLS = frozenset(", feed)
        self.assertIn("DHAN_VERIFIED_SYMBOLS = DHAN_VERIFIED_EQUITY_SYMBOLS | DHAN_VERIFIED_INDEX_SYMBOLS", feed)
        self.assertIn("if symbol not in DHAN_VERIFIED_SYMBOLS:", feed)
        self.assertIn("if interval not in (1, 5, 15, 25, 60):", feed)
        self.assertIn("symbol not in self._verified_dynamic_equities", feed)
        self.assertIn("self.verified_equity_symbol(symbol)", feed)
        self.assertIn('quote_timestamp": None', feed)
        self.assertIn('"freshness": "unverified"', feed)

    def test_dhan_batch_ltp_survives_history_refresh(self):
        self.assertIn('latest=dhan_batch_cache["quotes"].get(sym)', self.source)
        self.assertIn('data=dict(data,price=latest["price"],quote_timestamp=None,', self.source)
        self.assertIn('freshness="unverified",fetched_at=time.time())', self.source)

    def test_dhan_connect_settings_displays_partial_count(self):
        self.assertIn('f"Dhan connected • {received}/{total_symbols} LTP • "',self.source)
        self.assertIn('connection_status.color=GOLD if dhan_batch_issue[0] else GREEN',self.source)
        self.assertIn('f"Partial Clone B3 Dhan batch: {found}/{total} validated"',self.source)

    def test_dhan_connect_keeps_batch_in_new_scan_generation(self):
        # A provider switch creates the generation BEFORE the login snapshot.
        # A second generation bump after snapshot would incorrectly invalidate
        # the just-fetched data and cause a duplicate initial request.
        login=self.source.split('    async def check_clone_v2_connection():',1)[1].split('    def check_clone_v2_gateway(e):',1)[0]
        switch=login.index('provider_changed(None)')
        batch=login.index('dhan_batch_cache.update(',switch)
        finish=login.index('login_bootstrap.finish(provider_generation[0],"equities"',batch)
        self.assertLess(switch,batch)
        self.assertLess(batch,finish)
        self.assertNotIn('provider_generation[0]+=1',login[switch:finish])

    def test_dhan_connect_fetches_watchlist_batch(self):
        login=self.source.split('    async def check_clone_v2_connection():',1)[1].split('    def check_clone_v2_gateway(e):',1)[0]
        self.assertIn('selected_equities=list(all_watch_symbols())',login)
        self.assertIn('dhan_feed.paced_market_quotes,request_symbols',login)
        self.assertIn('dhan_batch_issue[0]=(',login)
        self.assertIn('watch_batch_status[0]=(',login)

    def test_batch_quote_health_is_not_overwritten_by_candle_failures(self):
        self.assertIn('batch_count=len(dhan_batch_cache["quotes"])', self.source)
        self.assertIn('historical candles unavailable', self.source)
        self.assertIn('dhan_batch_issue[0]=safe_error(exc)',self.source)
        self.assertIn('Dhan batch failed:',self.source)

    def test_oracle_assessment_poll_includes_selected_dynamic_equities(self):
        polling = ast.get_source_segment(self.source, self.functions["oracle_assessment_poll"])
        self.assertIn("sym in all_watch_symbols()", polling)
        self.assertIn("sym in DHAN_VERIFIED_SYMBOLS", polling)
        self.assertIn("dhan_feed.assessment,sym", polling)
        self.assertIn("oracle_assessment_attempts[key]<180", polling)
        coverage = ast.get_source_segment(self.source, self.functions["current_filter_coverage"])
        self.assertIn("analysis_audit.coverage(configured_scan_symbols())", coverage)

    def test_70_total_instruments_and_dynamic_scanner_roster(self):
        """70 unique NSE equities across lists, with 3 separate Dashboard indexes."""
        self.assertIn("MAX_WATCHLIST_EQUITIES=70", self.source)
        self.assertNotIn("MAX_WATCHLIST_EQUITIES=MAX_TOTAL_INSTRUMENTS-3", self.source)
        self.assertIn("normalize_watchlists(saved_watch_groups, maximum=70)", self.source)
        self.assertIn("normalize_watchlists(watch_groups, maximum=70)", self.source)
        self.assertIn("len(all_watch_symbols())>=MAX_WATCHLIST_EQUITIES", self.source)
        scanner = ast.get_source_segment(self.source, self.functions["configured_scan_symbols"])
        self.assertIn('["NIFTY","BANKNIFTY","SENSEX"]+all_watch_symbols()', scanner)
        self.assertNotIn("+watch_symbols)", scanner)
        self.assertIn("dict.fromkeys", scanner)
        self.assertIn("sym in group", ast.get_source_segment(
            self.source, self.functions["watch_symbol_owner"]))
        self.assertIn("verified_equity_symbol,sym", self.source)
        self.assertIn('selected_equities=list(all_watch_symbols())',self.source)
        self.assertIn('dhan_feed.paced_market_quotes,request_symbols',self.source)

    def test_dhan_super_five_ranking_uses_actual_saved_roster(self):
        # With five saved shares the Dhan ranking must not process the
        # other 46 fixed catalog equities; with seventy it must retain all.
        # This checks local rank selection, not Dhan request count or timing.
        self.assertIn('ranking_symbols=(all_watch_symbols() if prefs.get("source")=="Dhan"', self.source)
        self.assertIn('pairs=await asyncio.gather(*(rank_one(sym) for sym in ranking_symbols))', self.source)
        self.assertIn('total=len(ranking_symbols)', self.source)
        self.assertNotIn('pairs=await asyncio.gather(*(rank_one(sym) for sym in watch_symbols))', self.source)
        self.assertIn('symbols=configured_scan_symbols()', self.source)

    def test_dhan_history_cache_miss_requests_only_selected_equities(self):
        # A missing 45s quote cache must not request the fixed 51 snapshot
        # when only five shares are saved. The index quote lane is separate.
        source = self.source
        scan = source[source.index("    async def refresh_market():"):
                      source.index("    async def supervised_market_refresh():")]
        quote_stage = scan[scan.index('scan_progress["state"]="Checking Dhan batch before historical scan"'):
                           scan.index("# Connection is now ready: allow the first historical scan")]
        self.assertIn("selected_equities=all_watch_symbols()", quote_stage)
        self.assertIn("dhan_feed.equity_quotes_for_watchlist,selected_equities", quote_stage)
        self.assertNotIn("asyncio.to_thread(dhan_feed.batch_quotes)", quote_stage)
        self.assertIn('cached_batch if cached_batch is not None else', quote_stage)

    def test_dhan_super_five_saved_context_and_news_follow_active_equities(self):
        # Removed shares must not re-enter the five cards via saved ranking,
        # a default legacy placeholder, or a one-time news bootstrap.
        rank = ast.get_source_segment(self.source, self.functions["publish_partial_ranking"])
        news = ast.get_source_segment(self.source, self.functions["refresh_superfive_news"])
        card = ast.get_source_segment(self.source, self.functions["super_five_card"])
        self.assertIn("selected_equities=set(all_watch_symbols())", rank)
        self.assertIn('row["symbol"] in selected_equities', rank)
        self.assertIn('row.get("symbol") not in selected_equities', rank)
        self.assertIn("selected_news_symbols=all_watch_symbols()", news)
        self.assertIn("for sym in selected_news_symbols:", news)
        self.assertIn('row.get("symbol") in selected_news_symbols', news)
        self.assertIn('if prefs.get("source")=="Dhan" else watch_symbols', card)
        self.assertIn('if prefs.get("source")=="Dhan" else top5_candidates[:]', card)
        self.assertIn('row.get("symbol") in set(all_watch_symbols())', card)

    def test_empty_saved_watchlist_skips_equity_fetch(self):
        refresh=ast.get_source_segment(self.source,self.functions["refresh_watch_batch"])
        self.assertIn("if not requested_symbols:",refresh)
        self.assertIn("requested_symbols=priority_equity_batch(",refresh)
        self.assertIn('login_bootstrap.finish(provider_generation[0],"equities",0,0)',refresh)
        self.assertIn('Dhan equity fetch skipped',refresh)
        login=self.source.split("    async def check_clone_v2_connection():",1)[1].split("    def check_clone_v2_gateway(e):",1)[0]
        self.assertIn('selected_equities=list(all_watch_symbols())',login)
        self.assertIn('request_symbols=list(dict.fromkeys(',login)
        self.assertIn('login_bootstrap.finish(provider_generation[0],"equities",found,total)',login)
        self.assertNotIn('equity_quotes_for_watchlist,all_watch_symbols()',login)
        self.assertIn('if expected==0:',login)

    def test_history_cache_reuse_must_cover_newly_selected_equities(self):
        # A same-generation <45s cache is not complete when an equity was
        # added after its collection. Never reuse it as a complete roster.
        source = self.source
        scan = source[source.index("    async def refresh_market():"):
                      source.index("    async def supervised_market_refresh():")]
        stage = scan[scan.index('scan_progress["state"]="Checking Dhan batch before historical scan"'):
                     scan.index("# Connection is now ready: allow the first historical scan")]
        self.assertIn("selected_equities=all_watch_symbols()",stage)
        self.assertIn('set(selected_equities).issubset(dhan_batch_cache["quotes"])',stage)
        self.assertLess(stage.index("selected_equities=all_watch_symbols()"),
                        stage.index('cached_batch = (dict(dhan_batch_cache["quotes"])'))
        self.assertIn("dhan_feed.equity_quotes_for_watchlist,selected_equities",stage)

    def test_selected_quote_route_cooldown_gates_navigation_and_auto_poll(self):
        # No new network fanout: use both existing read-only endpoint cooldowns.
        navigation=self.source.split("    def render_page(i):",1)[1].split(
            "    def remember_scroll",1)[0] if False else self.source.split(
                "    def render_page(i):",1)[1].split("    def select(",1)[0]
        # render_page is followed by other functions; inspect just its own
        # launch guard rather than relying on unrelated cooldown code.
        begin=self.source.index("    def render_page(i):")
        end=self.source.index("    def remember_scroll",begin) if "    def remember_scroll" in self.source[begin:] else begin+4000
        launch=self.source[begin:begin+4500]
        self.assertIn('dhan_feed.cooldown_remaining("/v2/snapshot")==0',launch)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch")==0',launch)
        poll=ast.get_source_segment(self.source,self.functions["dhan_quote_poll"])
        self.assertIn('remaining=dhan_feed.cooldown_remaining("/v2/snapshot")',poll)
        self.assertIn('remaining=max(remaining,dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch"))',poll)
        self.assertLess(poll.index('remaining=max(remaining'),poll.index("if remaining==0:"))

    def test_login_resume_index_cooldown_is_not_ignored(self):
        index=ast.get_source_segment(self.source,self.functions["refresh_dhan_index_quotes"])
        resume=ast.get_source_segment(self.source,self.functions["refresh_after_resume"])
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/index-ltp-batch")',index)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch")==0',resume)
        self.assertIn('await refresh_dhan_index_quotes()',resume)
        self.assertLess(index.index('if index_cooldown>0:'),
                        index.index('index_refresh_busy[0]=True'))

    def test_manual_refresh_respects_selected_equity_route_cooldown(self):
        # Manual and automatic demand share the same broker-safe 429 clock.
        manual=ast.get_source_segment(self.source,self.functions["refresh_all_dhan_quotes"])
        self.assertIn('cooldown=dhan_feed.cooldown_remaining("/v2/snapshot")',manual)
        self.assertIn('cooldown=max(cooldown,dhan_feed.cooldown_remaining("/dhan/selected-ltp-batch"))',manual)
        self.assertIn('index_cooldown=dhan_feed.cooldown_remaining("/dhan/index-ltp-batch")',manual)
        self.assertIn('if cooldown>0 and index_cooldown>0:',manual)
        self.assertIn('if cooldown==0:',manual)
        self.assertIn('if index_cooldown==0:',manual)
        self.assertLess(manual.index('if cooldown==0:'),manual.index('await refresh_watch_batch()'))
        self.assertLess(manual.index('if index_cooldown==0:'),manual.index('await refresh_dhan_index_quotes(force=True)'))
        self.assertIn('if cooldown==0 and not refresh_hours() and current[0]==4:',manual)
        self.assertIn('manual_quote_last_attempt[0]=now',manual)
        # The global cooldown is included by the transport, but an equity-only
        # backoff cannot suppress the independent three-index batch.
        feed=(SOURCE.parent / "server_feed.py").read_text(encoding="utf-8")
        self.assertIn('self._global_cooldown_until',feed)
        self.assertIn('"/dhan/index-ltp-batch"',feed)
        self.assertLess(manual.index('if cooldown>0 and index_cooldown>0:'),
                        manual.index('if index_cooldown==0:'))
        self.assertLess(manual.index('if cooldown>0 and index_cooldown>0:'),manual.index('manual_quote_last_attempt[0]=now'))

    def test_known_symbols_are_unique(self):
        assign = next(node for node in ast.walk(self.tree)
                      if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "watch_symbols"
                              for t in node.targets))
        symbols = ast.literal_eval(assign.value)
        self.assertEqual(len(symbols), 51)
        self.assertEqual(len(set(symbols)), len(symbols))


if __name__ == "__main__":
    unittest.main()
