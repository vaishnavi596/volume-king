"""Actual historical evidence replay remains separate from synthetic policy tests."""
import unittest,sys,pathlib,ast
from datetime import datetime,timezone,timedelta
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_historical_vote_replay import historical_vote_replay,simulated_conflict_policy_matrix
IST=timezone(timedelta(hours=5,minutes=30))
def bars():
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    arr=[]
    for i in range(375):
        p=25350+(i%5)
        arr.append([start+i*60,p,p+2,p-2,p+1 if i%2 else p-1,916+i])
    return arr

def replay(**kwargs):
    params=dict(symbol="NIFTY",timeframe="1m",generation=1,
                source="Dhan",bars=bars(),filter_rows=[
                    {"name":"MACD","vote":1},{"name":"VWAP","vote":-1},
                    {"name":"Pivot Points","vote":-1},
                    {"name":"OI Support","vote":None}])
    params.update(kwargs)
    return historical_vote_replay(**params)

class HistoricalVotingTests(unittest.TestCase):
    def test_real_historical_technical_and_candle_vote_not_live(self):
        r=replay()
        self.assertEqual(r["technical_vote"]["bullish"],33)
        self.assertEqual(r["technical_vote"]["bearish"],67)
        self.assertTrue(r["technical_vote"]["historical"])
        self.assertEqual(r["boxes"][0]["state"],"HIST_VOTE")
        self.assertEqual(r["boxes"][1]["state"],"HIST_VOTE")
        self.assertEqual(r["boxes"][2]["state"],"WAIT")
        self.assertEqual(r["combined"]["state"],"WAIT")
        self.assertEqual(r["combined"]["coverage"],2)
        self.assertFalse(r["verified_live"])
        self.assertEqual(r["provider_requests"],0)
    def test_independent_historical_four_box_evidence_contract(self):
        session=bars()
        stamp=session[-1][0]
        def evidence(name, basis, **extra):
            return dict(source="Dhan",verified=True,historical=True,
                        symbol="NIFTY",timeframe="1m",generation=1,
                        timestamp=stamp,bullish=75,bearish=25,
                        direction_basis=basis,**extra)
        hist=dict(
            news=evidence("news","verified_symbol_news_impact"),
            futures=evidence("futures","validated_futures_trade_flow",
                             contract="NIFTY-FUT-202611"),
            options=evidence("options","validated_option_trade_flow",
                             contract="NIFTY-25350-CE",expiry="2026-11-23",
                             underlying="NIFTY"))
        result=replay(historical_context=hist)
        self.assertEqual([v["state"] for v in result["boxes"]],
                         ["HIST_VOTE","HIST_VOTE","HIST_VOTE","HIST_VOTE","HIST_VOTE"])
        self.assertTrue(all(v["eligible_live"] is False for v in result["boxes"]))
        self.assertFalse(result["verified_live"])
        self.assertEqual(result["combined"]["state"],"WAIT")
        self.assertEqual(result["combined"]["coverage"],5)
        self.assertEqual(result["historical_combined"]["coverage"],5)
        self.assertEqual(result["historical_combined"]["mode"],"HIST_ONLY_NOT_LIVE")
        self.assertIn(result["historical_combined"]["state"],("BULLISH","BEARISH","WAIT"))
        self.assertEqual(result["orders_sent"],0)

    def test_three_independent_historical_engines_can_vote_hist_not_live(self):
        sample=bars()
        stamp=sample[-1][0]
        context={"news":{"source":"Dhan","verified":True,"historical":True,
                         "symbol":"NIFTY","timeframe":"1m","generation":1,
                         "timestamp":stamp,"bullish":95,"bearish":5,
                         "direction_basis":"verified_symbol_news_impact"}}
        result=replay(historical_context=context,
                      filter_rows=[{"name":"EMA 9/21","vote":1},
                                   {"name":"MACD","vote":1},
                                   {"name":"RSI 14","vote":1}])
        self.assertEqual(result["historical_combined"]["coverage"],3)
        self.assertEqual(result["historical_combined"]["mode"],"HIST_ONLY_NOT_LIVE")
        self.assertEqual(result["combined"]["state"],"WAIT")
        self.assertFalse(result["verified_live"])
        self.assertEqual(result["orders_sent"],0)
        self.assertEqual(result["provider_requests"],0)

    def test_historical_vote_stays_wait_without_verified_third_source(self):
        result=replay()
        self.assertEqual(result["historical_combined"]["coverage"],2)
        self.assertEqual(result["historical_combined"]["state"],"WAIT")
        self.assertEqual(result["historical_combined"]["reason"],
                         "Insufficient verified engines")
        self.assertEqual(result["partial_technical_direction"]["state"],"BEARISH")
        self.assertEqual(result["partial_technical_direction"]["mode"],"TECHNICAL_HIST_ONLY_NOT_LIVE")
        self.assertEqual(result["combined"]["state"],"WAIT")

    def test_option_historical_expiry_is_canonical_and_not_expired(self):
        stamp=bars()[-1][0]
        valid=dict(source="Dhan",verified=True,historical=True,
                   symbol="NIFTY",timeframe="1m",generation=1,
                   timestamp=stamp,bullish=80,bearish=20,
                   direction_basis="validated_option_trade_flow",
                   contract="NIFTY-CE",expiry="2026-11-26",
                   underlying="NIFTY")
        self.assertEqual(replay(historical_context={"options":valid})
                         ["boxes"][4]["state"],"HIST_VOTE")
        for bad in ("2020-01-01","2026-11-23T00:00:00",
                    "bad-expiry","",None,True):
            with self.subTest(expiry=bad):
                result=replay(historical_context={
                    "options":dict(valid,expiry=bad)})
                self.assertEqual(result["boxes"][4]["state"],"WAIT")
                self.assertEqual(result["historical_combined"]["state"],"WAIT")

    def test_unverified_context_never_claims_four_box_votes(self):
        # Data-only context and mismatched proof never vote.
        bad=dict(news={"headlines":20,"direction":"BULLISH"},
                 futures={"source":"Dhan","price":25300},
                 options={"source":"Dhan","pcr":1.5,"max_pain":25350})
        result=replay(historical_context=bad)
        self.assertEqual([v["state"] for v in result["boxes"]][2:],
                         ["WAIT","WAIT","WAIT"])
        self.assertEqual(result["boxes"][2]["reason"],
                         "VERIFIED_HISTORICAL_NEWS_IMPACT_MISSING")
        self.assertEqual(result["boxes"][3]["reason"],
                         "VERIFIED_HISTORICAL_FUTURES_FLOW_MISSING")
        self.assertEqual(result["boxes"][4]["reason"],
                         "VERIFIED_EXPIRY_SCOPED_OPTION_FLOW_MISSING")
        valid=dict(source="Dhan",verified=True,historical=True,
                   symbol="NIFTY",timeframe="1m",generation=1,
                   timestamp=bars()[-1][0],bullish=70,bearish=30,
                   direction_basis="validated_option_trade_flow",
                   contract="NIFTY-CE",expiry="2026-11-23",
                   underlying="NIFTY")
        for change in ({"generation":2},{"symbol":"BANKNIFTY"},
                       {"timestamp":bars()[-1][0]+100},
                       {"verified":False},{"expiry":""},
                       {"underlying":"RELIANCE"},{"direction_basis":"pcr"},
                       {"bearish":40}):
            row=dict(valid,**change)
            self.assertEqual(replay(historical_context={"options":row})
                             ["boxes"][4]["state"],"WAIT")

    def test_candle_hist_replay_rejects_irregular_last_eight(self):
        original=bars()
        regular=replay(bars=original)
        self.assertEqual(regular["boxes"][1]["state"],"HIST_VOTE")
        shifted=[row[:] for row in original]
        shifted[-4][0]+=1  # 61s then 59s: monotonic but not exact 1m
        replayed=replay(bars=shifted)
        self.assertEqual(replayed["boxes"][0]["state"],"HIST_VOTE")
        self.assertEqual(replayed["boxes"][1]["state"],"WAIT")
        self.assertEqual(replayed["boxes"][1]["reason"],
                         "HIST_CANDLE_SAMPLE_NONCONTIGUOUS")
        self.assertEqual(replayed["combined"]["state"],"WAIT")
        self.assertEqual(replayed["provider_requests"],0)
        self.assertEqual(replayed["orders_sent"],0)
        self.assertEqual(shifted[-4][0],original[-4][0]+1)

    def test_only_thirteen_candle_filters_can_enter_technical_hist_vote(self):
        # An integer in an RSS or option context row is not technical evidence.
        filters=[
            {"name":"MACD","vote":1},
            {"name":"VWAP","vote":-1},
            {"name":"News Headlines","vote":1},
            {"name":"OI Support","vote":1},
            {"name":"OI Resistance","vote":-1},
            {"name":"OI Profile","vote":1},
            {"name":"Dhan Max Pain","vote":-1}]
        original=[dict(row) for row in filters]
        result=replay(filter_rows=filters)
        self.assertEqual(result["technical_vote"]["bullish"],50)
        self.assertEqual(result["technical_vote"]["bearish"],50)
        self.assertEqual(result["technical_vote"]["directional_count"],2)
        self.assertEqual(result["boxes"][2]["state"],"WAIT")
        self.assertEqual(result["boxes"][4]["state"],"WAIT")
        self.assertEqual(filters,original)
        self.assertEqual(result["orders_sent"],0)

    def test_unknown_candle_filter_cannot_inject_direction(self):
        result=replay(filter_rows=[
            {"name":"MACD","vote":-1},
            {"name":"INJECTED_CONTEXT_VOTE","vote":1}])
        self.assertEqual(result["technical_vote"]["bullish"],0)
        self.assertEqual(result["technical_vote"]["bearish"],100)
        self.assertEqual(result["technical_vote"]["directional_count"],1)

    def test_forming_bar_excluded_without_promoting_old_technical_votes(self):
        arr=bars()
        before=[row[:] for row in arr]
        r=replay(bars=arr,history_timestamp=arr[-1][0]+10)
        self.assertEqual(r["excluded_forming_candle_bars"],1)
        self.assertEqual(r["boxes"][0]["state"],"HIST_VOTE")
        self.assertEqual(r["boxes"][1]["state"],"HIST_VOTE")
        self.assertEqual(r["historical_session_bars"],374)
        self.assertTrue(r["technical_recomputed_from_completed_bars"])
        self.assertNotIn("TECHNICAL_FILTERS_RECALC_ON_COMPLETED_BARS_REQUIRED",
                         r["blockers"])
        self.assertEqual(r["orders_sent"],0)
        self.assertEqual(arr,before)

    def test_completed_phone_replay_recalculates_without_stale_filter_votes(self):
        arr=bars()
        bogus=[{"name":"MACD","vote":1},
               {"name":"EMA 9/21","vote":1},
               {"name":"RSI 14","vote":1},
               {"name":"News Headlines","vote":1},
               {"name":"OI Support","vote":1}]
        result=replay(bars=arr,filter_rows=bogus,
                      history_timestamp=arr[-1][0]+60)
        self.assertTrue(result["technical_recomputed_from_completed_bars"])
        from scanner_engine import analyze
        expected=analyze(arr,["MACD","EMA 9/21","RSI 14"],"1m")
        directional=[row["vote"] for row in expected["votes"]
                     if row.get("vote") in (-1,1)]
        self.assertEqual(result["technical_vote"]["directional_count"],
                         len(directional))
        self.assertEqual(result["technical_vote"]["bullish"],
                         round(100*sum(v==1 for v in directional)/len(directional)))
        self.assertEqual(result["boxes"][2]["state"],"WAIT")
        self.assertEqual(result["boxes"][4]["state"],"WAIT")
        self.assertEqual(result["provider_requests"],0)

    def test_phone_replay_malformed_technical_series_stays_wait(self):
        arr=bars()
        arr[-25][2]=arr[-25][1]-1  # high below open, invalid historic OHLC
        result=replay(bars=arr,
                      history_timestamp=arr[-1][0]+60)
        self.assertFalse(result["technical_recomputed_from_completed_bars"])
        self.assertEqual(result["boxes"][0]["state"],"WAIT")
        self.assertEqual(result["orders_sent"],0)
        self.assertEqual(len(result["boxes"]),5)
        self.assertTrue(all(box["state"]=="WAIT" and not box["eligible_live"] for box in result["boxes"]))
        self.assertIn("HIST_OHLCV_INVALID",result["blockers"])
        self.assertEqual(result["historical_combined"]["state"],"WAIT")

    def test_forming_bar_recalculation_rejects_context_only_filter_votes(self):
        arr=bars()
        selected=[{"name":"MACD","vote":-1},
                  {"name":"News Headlines","vote":1},
                  {"name":"OI Support","vote":1},
                  {"name":"Dhan Max Pain","vote":1}]
        output=replay(bars=arr,filter_rows=selected,
                      history_timestamp=arr[-1][0]+5)
        self.assertTrue(output["technical_recomputed_from_completed_bars"])
        self.assertLessEqual(output["technical_vote"]["directional_count"],1)
        self.assertEqual(output["boxes"][2]["state"],"WAIT")
        self.assertEqual(output["boxes"][4]["state"],"WAIT")
        self.assertEqual(output["provider_requests"],0)
        self.assertEqual(output["orders_sent"],0)

    def test_forming_bar_without_selected_technical_keeps_T_wait(self):
        arr=bars()
        output=replay(bars=arr,
                      filter_rows=[{"name":"News Headlines","vote":1}],
                      history_timestamp=arr[-1][0]+5)
        self.assertFalse(output["technical_recomputed_from_completed_bars"])
        self.assertEqual(output["boxes"][0]["state"],"WAIT")
        self.assertEqual(output["boxes"][1]["state"],"HIST_VOTE")
        self.assertIn("TECHNICAL_FILTERS_RECALC_ON_COMPLETED_BARS_REQUIRED",
                      output["blockers"])

    def test_future_dated_and_bad_observation_fail_closed(self):
        arr=bars()
        r=replay(bars=arr,history_timestamp=arr[-1][0]-10)
        self.assertEqual(r["boxes"],[])
        self.assertIn("FUTURE_DATED_HIST_CANDLE_NOT_VERIFIED",r["blockers"])
        for stamp in (0,-1,True,float("nan"),float("inf"),"2026-11-23"):
            with self.subTest(stamp=stamp):
                with self.assertRaises(ValueError):
                    replay(history_timestamp=stamp)

    def test_completed_bar_keeps_T_and_C_hist(self):
        arr=bars()
        r=replay(bars=arr,history_timestamp=arr[-1][0]+60)
        self.assertEqual(r["excluded_forming_candle_bars"],0)
        self.assertEqual([row["state"] for row in r["boxes"][:2]],
                         ["HIST_VOTE","HIST_VOTE"])

    def test_candle_doji_wait_has_distinct_reason(self):
        rows=bars()
        for b in rows[-8:]:
            b[4]=b[1]
        result=replay(bars=rows)
        self.assertEqual(result["boxes"][1]["state"],"WAIT")
        self.assertEqual(result["boxes"][1]["reason"],
                         "INSUFFICIENT_VALID_COMPLETED_DIRECTIONAL_CANDLES")
    def test_non_session_tail_excluded_without_mutating(self):
        arr=bars()
        arr.append([int(datetime(2026,11,23,19,57,tzinfo=IST).timestamp()),
                    25349.65,25349.65,25349.65,25349.65,0])
        before=[v[:] for v in arr]
        r=replay(bars=arr)
        self.assertEqual(r["removed_outside_session_bars"],1)
        self.assertEqual(arr,before)
    def test_missing_data_never_invents_five_live_votes(self):
        r=replay(source="Yahoo")
        self.assertEqual(r["boxes"],[])
        self.assertEqual(r["combined"]["state"],"WAIT")
    def test_synthetic_policy_is_very_explicitly_not_live(self):
        s=simulated_conflict_policy_matrix()
        self.assertEqual(s["results"]["FOUR_BULL_ONE_BEAR"],"BULLISH")
        self.assertEqual(s["results"]["THREE_BULL_TWO_BEAR"],"WAIT")
        self.assertEqual(s["results"]["FOUR_BEAR_ONE_BULL"],"BEARISH")
        self.assertFalse(s["live_verified"])
    def test_scanner_renders_real_historical_final_replay_separately(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        self.assertIn("def scanner_historical_final_vote(symbol=None, timeframe=None):",source)
        self.assertIn('final=output["historical_combined"]',source)
        self.assertIn('output=cached_historical_final_replay(',source)
        self.assertIn('filter_rows=selected,history_timestamp=now)',source)
        self.assertIn('scanner_historical_final_vote()],spacing=5)))',source)
        block=source.split("    def scanner_historical_final_vote(symbol=None, timeframe=None):",1)[1].split("    def five_engine_chips(",1)[0]
        self.assertIn('" • NOT LIVE"',block)
        self.assertIn('option_label=historical_option_summary(sym)',block)
        self.assertIn('(" | "+option_label if option_label else "")',block)
        self.assertIn('history=shared_history(sym,frame)',block)
        self.assertNotIn('get_market_data(',block)
        self.assertNotIn('dhan_feed.',block)
        self.assertNotIn('orders_sent(',block)

    def test_unsupported_final_frame_returns_before_history_read(self):
        import textwrap
        from types import SimpleNamespace
        from unittest.mock import Mock
        source=(ROOT/"src/main.py").read_text()
        node=next(n for n in ast.walk(ast.parse(source))
                  if isinstance(n,ast.FunctionDef) and n.name=="scanner_historical_final_vote")
        history=Mock(side_effect=AssertionError("unsupported frame must not read history"))
        replay=Mock(side_effect=AssertionError("unsupported frame must not replay"))
        scope=dict(prefs={},note=lambda s:s,shared_history=history,
                   cached_historical_final_replay=replay,
                   scan_symbol=SimpleNamespace(value="NIFTY"),
                   scan_tf=SimpleNamespace(value="15m"))
        exec(compile(textwrap.dedent(ast.get_source_segment(source,node)),"final_vote","exec"),scope)
        fn=scope[node.name]
        for frame in ("2m","10m","15m","30m","1h","invalid"):
            with self.subTest(frame=frame):
                self.assertIn("unsupported selected timeframe",fn("NIFTY",frame))
        self.assertIn("NOT LIVE",fn())
        history.assert_not_called()
        replay.assert_not_called()

    def test_historical_final_replay_cache_bounds_and_revision_gates(self):
        s=(ROOT/"src/main.py").read_text()
        ast.parse(s)
        cache=s.split("    def cached_historical_final_replay(",1)[1].split(
            "    def canonical_live_final_note(",1)[0]
        self.assertIn('key=(sym,frame)',cache)
        self.assertIn('provider_generation[0]',cache)
        self.assertIn('prefs.get("source")',cache)
        self.assertIn('tuple(row["name"] for row in selected)',cache)
        self.assertIn('fingerprint=tuple(tuple(bar)',cache)
        self.assertIn('last_stamp+seconds<=now',cache)
        self.assertIn('cached[0]==identity',cache)
        self.assertIn('len(historical_final_replay_cache)>=220',cache)
        self.assertIn('historical_final_replay_cache.clear()',cache)
        self.assertIn('history_timestamp=now',cache)
        self.assertNotIn('get_market_data(',cache)
        self.assertNotIn('dhan_feed.',cache)

    def test_shared_final_cache_rejects_wrong_frame_and_source(self):
        import math
        import textwrap
        from unittest.mock import patch
        source=(ROOT/"src/main.py").read_text()
        node=next(n for n in ast.walk(ast.parse(source))
                  if isinstance(n,ast.FunctionDef) and n.name=="cached_historical_final_replay")
        scope=dict(math=math,provider_generation=[1],prefs={"source":"Dhan"},
                   historical_final_replay_cache={})
        exec(compile(textwrap.dedent(ast.get_source_segment(source,node)),"replay","exec"),scope)
        fn=scope[node.name]
        data={"source":"Dhan","_scanner_timeframe":"1m","bars":bars()}
        stamp=data["bars"][-1][0]
        selected=[{"name":"MACD"}]
        with patch("v3_historical_vote_replay.historical_vote_replay",
                   side_effect=lambda **kw:kw) as replay_mock:
            good=fn("NIFTY","1m",data,selected,stamp+60)
            self.assertEqual(good["source"],"Dhan")
            self.assertIs(fn("NIFTY","1m",data,selected,stamp+60),good)
            wrong=fn("NIFTY","1m",dict(data,_scanner_timeframe="5m"),selected,stamp+60)
            self.assertIsNone(wrong["source"])
            self.assertIsNone(wrong["bars"])
            self.assertEqual(replay_mock.call_count,2)
            # Wrong incoming provider and wrong frame share the same rejected evidence.
            foreign=fn("NIFTY","1m",dict(data,source="Yahoo Finance"),selected,stamp+60)
            self.assertIs(foreign,wrong)
            self.assertIsNone(foreign["bars"])
            self.assertEqual(replay_mock.call_count,2)
            scope["prefs"]["source"]="Yahoo Finance"
            inactive=fn("NIFTY","1m",data,selected,stamp+60)
            self.assertIsNone(inactive["source"])
            self.assertIsNone(inactive["bars"])
            self.assertEqual(replay_mock.call_count,3)
            scope["prefs"]["source"]="Dhan"
            recovered=fn("NIFTY","1m",data,selected,stamp+60)
            self.assertEqual(recovered["source"],"Dhan")
            self.assertEqual(recovered["bars"],data["bars"])
            self.assertEqual(replay_mock.call_count,4)
            future=fn("NIFTY","1m",data,selected,stamp-1)
            forming=fn("NIFTY","1m",data,selected,stamp+1)
            self.assertIsNot(future,forming)
            self.assertEqual(replay_mock.call_count,6)

    def test_shared_final_renderers_preserve_exact_identity_and_modes(self):
        import math
        import textwrap
        from types import SimpleNamespace
        from unittest.mock import Mock
        from filter_wiring_audit import CANDLE_FILTERS
        source=(ROOT/"src/main.py").read_text()
        tree=ast.parse(source)
        names=("cached_historical_final_replay","canonical_live_final_note",
               "scanner_historical_final_vote")
        stamp=bars()[-1][0]+300
        history=Mock(side_effect=lambda sym,frame:{
            "source":"Dhan","_scanner_timeframe":frame,"bars":bars()})
        live=Mock(return_value={"combined":{"state":"WAIT","coverage":0,
                    "reason":"fixture missing live evidence"}})
        selected=[name for name in ("MACD","VWAP") if name in CANDLE_FILTERS]
        scope=dict(math=math,provider_generation=[1],prefs={"source":"Dhan"},
                   historical_final_replay_cache={},note=lambda s:s,
                   shared_history=history,read_five_engine_context=live,
                   dhan_feed=SimpleNamespace(connected=True),
                   scan_symbol=SimpleNamespace(value="NIFTY"),
                   scan_tf=SimpleNamespace(value="1m"),
                   filter_selected=selected,filter_modes={},
                   historical_option_summary=lambda sym:"",
                   time=SimpleNamespace(time=lambda:stamp))
        for name in names:
            node=next(n for n in ast.walk(tree)
                      if isinstance(n,ast.FunctionDef) and n.name==name)
            exec(compile(textwrap.dedent(ast.get_source_segment(source,node)),
                         name,"exec"),scope)
        hist=scope[names[2]]
        live_note=scope[names[1]]
        # Explicit calls match the shared Dashboard/Watchlist/Super Five
        # contracts; Scanner supplies its current selection by default.
        for frame in ("1m","3m","5m"):
            with self.subTest(frame=frame):
                scope["scan_tf"].value=frame
                explicit=hist("NIFTY",frame)
                self.assertEqual(explicit,hist())
                self.assertIn("NIFTY "+frame,explicit)
                self.assertIn("NOT LIVE",explicit)
                history.assert_called_with("NIFTY",frame)
                self.assertIn("NIFTY "+frame,live_note("NIFTY",frame))
                live.assert_called_with("NIFTY",frame)
        self.assertEqual(set(scope["historical_final_replay_cache"]),
                         {("NIFTY",f) for f in ("1m","3m","5m")})
        # Disconnection must not destroy HIST or request live evidence.
        previous=hist("NIFTY","3m")
        scope["dhan_feed"].connected=False
        live.reset_mock()
        self.assertIn("0/5 verified",live_note("NIFTY","3m"))
        live.assert_not_called()
        self.assertEqual(previous,hist("NIFTY","3m"))
        scope["dhan_feed"].connected=True
        scope["prefs"]["market_display_mode"]="HISTORICAL"
        self.assertIn("DISABLED",live_note("NIFTY","3m"))
        live.assert_not_called()
        scope["prefs"]["market_display_mode"]="LIVE_ONLY"
        history.reset_mock()
        self.assertIn("HIDDEN",hist("NIFTY","3m"))
        history.assert_not_called()

    def test_historical_final_is_same_function_on_all_four_surfaces(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        for call in ('scanner_historical_final_vote(index_name,"1m")',
                     'scanner_historical_final_vote(sym,"1m")',
                     'scanner_historical_final_vote(sym,"1m")',
                     'scanner_historical_final_vote(row["symbol"],"5m")',
                     'scanner_historical_final_vote()],spacing=5)))'):
            with self.subTest(call=call):
                self.assertIn(call,source)
        self.assertIn('five_cell=ft.Container(content=ft.Column([',source)
        self.assertIn('five.content=ft.Column([',source)
        self.assertIn('sym=str(symbol or scan_symbol.value or "NIFTY")',source)
        self.assertIn('frame=str(timeframe or scan_tf.value or "1m")',source)

    def test_b178_and_master_doctors_integrate_same_historical_replay(self):
        s=(ROOT/"src/main.py").read_text()
        ast.parse(s)
        self.assertIn('source=history.get("source"),bars=bars,',s)
        self.assertNotIn('source=history.get("source"),bars=completed_bars,',s)
        self.assertIn('offline_candle=completed_timeframe_candle_balance(',s)
        self.assertIn('offline_5m=shared_history(symbol,"5m")',s)
        self.assertIn('Candle HIST "+display_timeframe+" B"',s)
        self.assertIn('Candle HIST 5m B"',s)
        self.assertIn('N/F/O WAIT (independent evidence unavailable)',s)
        self.assertIn('News HIST WAIT (verified impact missing)',s)
        self.assertIn('Futures HIST WAIT (measured flow missing)',s)
        self.assertIn('Options HIST WAIT (expiry-specific trade flow missing;',s)
        self.assertIn('"historical_vote_replay":historical_replay',s)
        self.assertIn('"historical_vote_replay":master_historical_replay',s)
        self.assertIn('"voting_policy_self_test":simulated_conflict_policy_matrix()',s)
if __name__=="__main__":unittest.main()


class R2MalformedHistoricalInputTests(unittest.TestCase):
    def test_malformed_last_or_interior_row_abstains_without_crashing(self):
        for index in (-1,-2,30):
            for bad in (None,[],["bad",1,2,1,2,3],
                        [float("nan"),1,2,1,2,3],
                        [float("inf"),1,2,1,2,3]):
                with self.subTest(index=index,bad=bad):
                    sample=bars()
                    cutoff=sample[-1][0]+60
                    sample[index]=bad
                    result=replay(bars=sample,history_timestamp=cutoff)
                    self.assertEqual(result["combined"]["state"],"WAIT")
                    self.assertEqual(result["historical_combined"]["coverage"],0)
                    self.assertIn("COMPLETED_SESSION_HISTORY_INVALID_OR_LT_30",
                                  result["blockers"])
                    self.assertFalse(result["verified_live"])


class R2HistoricalFlowModeTests(unittest.TestCase):
    def test_contradictory_live_flags_do_not_enter_historical_quorum(self):
        from v3_historical_vote_replay import _historical_measured, HIST_BASES
        stamp=1795000000
        row=dict(verified=True,source="Dhan",historical=True,
                 direction_basis=HIST_BASES["futures"],symbol="NIFTY",timeframe="5m",
                 generation=3,timestamp=stamp,contract="NIFTY-FUT",bullish=75,bearish=25)
        args=dict(symbol="NIFTY",timeframe="5m",generation=3,last_bar=stamp)
        self.assertIsNotNone(_historical_measured("futures",row,**args))
        for flag in ("live_verified","verified_live"):
            self.assertIsNone(_historical_measured("futures",dict(row,**{flag:True}),**args))
