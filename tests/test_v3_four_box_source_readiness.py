"""B178/master four-box ingress visibility cannot invent provider proof."""
import pathlib
import sys
import unittest
from datetime import datetime, timezone, timedelta

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_four_box_source_readiness import four_box_source_readiness

IST=timezone(timedelta(hours=5,minutes=30))


def history(tf="1m"):
    seconds={"1m":60,"3m":180,"5m":300}[tf]
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    return dict(source="Dhan",_scanner_timeframe=tf,
                bars=[[start+i*seconds,100,103,99,101,300+i] for i in range(40)])


class FourBoxSourceContracts(unittest.TestCase):
    def test_exact_frame_c_has_real_hist_and_nfo_only_context(self):
        h=history()
        last=h["bars"][-1][0]+60
        x=four_box_source_readiness(
            symbol="NIFTY",timeframe="1m",generation=3,history=h,
            news_cache={"items":[{"title":"One", "url":"https://example.org/a",
                                  "published":last-60,"source":"RSS Publisher"}]},
            futures_cache=dict(source="Dhan",symbol="NIFTY",underlying="NIFTY",
                               exchange_segment="NSE_FNO",expiry="2026-12-31",
                               mapping_verified=True,contract="NIFTY-FUT",
                               ltp=25600.5,freshness="unverified",direction=None,
                               direction_verified=False,signal_eligible=False,
                               live_orders_enabled=False),
            option_context=dict(source="dhan",symbol="NIFTY",
                                expiry="2026-11-26",signal_eligible=False),
            now=last)
        self.assertTrue(x["box_sources"]["C"]["historical_direction_available"])
        self.assertEqual(x["box_sources"]["C"]["historical_bullish"],100)
        for name in ("N","F","O"):
            self.assertTrue(x["box_sources"][name]["cache_present"])
            self.assertFalse(x["box_sources"][name]["historical_direction_available"])
            self.assertFalse(x["box_sources"][name]["live_direction_verified"])
        self.assertEqual(x["live_vote_count"],0)
        self.assertEqual(x["provider_requests"],0)
        self.assertEqual(x["orders_sent"],0)

    def test_news_context_requires_valid_recent_unique_rss_rows(self):
        h=history()
        now=h["bars"][-1][0]+60
        valid={"title":"Nifty earnings","url":"https://example.org/a",
               "source":"RSS Publisher","published":now-60}
        invalid=[42,{"title":"no date","url":"https://example.org/b",
                     "source":"RSS","published":None},
                 dict(valid,published=now-86401),dict(valid,published=now+30),
                 dict(valid,url="http://unsafe.example/a"),
                 dict(valid,source=""),dict(valid,title=" ")]
        x=four_box_source_readiness(
            symbol="NIFTY",timeframe="1m",generation=3,history=h,
            news_cache={"items":invalid+[valid,dict(valid,title=" NIFTY   EARNINGS ")]},
            now=now)
        self.assertEqual(x["box_sources"]["N"]["context_count"],1)
        self.assertTrue(x["box_sources"]["N"]["cache_present"])
        self.assertFalse(x["box_sources"]["N"]["live_direction_verified"])
        self.assertEqual(x["live_vote_count"],0)
        x=four_box_source_readiness(
            symbol="NIFTY",timeframe="1m",generation=3,history=h,
            news_cache={"items":invalid},now=now)
        self.assertEqual(x["box_sources"]["N"]["context_count"],0)
        self.assertFalse(x["box_sources"]["N"]["cache_present"])
        self.assertEqual(x["box_sources"]["N"]["blocker"],
                         "SYMBOL_NEWS_HEADLINES_MISSING")
        self.assertEqual(x["provider_requests"],0)
        self.assertEqual(x["orders_sent"],0)

    def test_cross_timeframe_and_expiry_context_fails_closed(self):
        h=history("1m")
        now=h["bars"][-1][0]+60
        x=four_box_source_readiness(
            symbol="BANKNIFTY",timeframe="3m",generation=3,history=h,
            news_cache={"items":[1,2]},
            futures_cache=dict(source="Dhan",symbol="NIFTY",underlying="NIFTY",
                               exchange_segment="NSE_FNO",expiry="2026-12-31",
                               mapping_verified=True,contract="NIFTY-FUT",
                               ltp=25600.5,freshness="unverified",direction=None,
                               direction_verified=False,signal_eligible=False,
                               live_orders_enabled=False),
            option_context=dict(source="dhan",symbol="NIFTY",expiry="2026-11-26",
                                signal_eligible=False),now=now)
        self.assertFalse(x["box_sources"]["C"]["cache_present"])
        self.assertEqual(x["box_sources"]["C"]["blocker"],
                         "EXACT_FRAME_DHAN_CANDLES_MISSING")
        self.assertFalse(x["box_sources"]["F"]["cache_present"])
        self.assertFalse(x["box_sources"]["O"]["cache_present"])
        self.assertFalse(x["box_sources"]["N"]["historical_direction_available"])

    def test_unsafe_futures_context_never_counts_as_present(self):
        h=history()
        valid=dict(source="Dhan",symbol="NIFTY",underlying="NIFTY",
                   exchange_segment="NSE_FNO",expiry="2026-12-31",
                   mapping_verified=True,contract="NIFTY-FUT",ltp=25600.5,
                   freshness="unverified",direction=None,
                   direction_verified=False,signal_eligible=False,
                   live_orders_enabled=False)
        for patch in ({"expiry":"not-a-date"},{"expiry":"2020-01-01"},
                      {"symbol":"BANKNIFTY"},
                      {"exchange_segment":"NSE_EQ"},{"ltp":True},{"ltp":0},
                      {"ltp":float("nan")},{"direction":"BULLISH"},
                      {"direction_verified":True},{"signal_eligible":True},
                      {"live_orders_enabled":True},{"freshness":"verified_live"}):
            with self.subTest(patch=patch):
                result=four_box_source_readiness(
                    symbol="NIFTY",timeframe="1m",generation=3,history=h,
                    futures_cache=dict(valid,**patch),
                    now=h["bars"][-1][0]+60)
                self.assertFalse(result["box_sources"]["F"]["cache_present"])
                self.assertEqual(result["live_vote_count"],0)

    def test_invalid_or_expired_option_expiry_is_not_cache_ready(self):
        h=history()
        now=h["bars"][-1][0]+60
        valid=dict(source="dhan",symbol="NIFTY",expiry="2026-11-26",
                   signal_eligible=False)
        self.assertTrue(four_box_source_readiness(
            symbol="NIFTY",timeframe="1m",generation=3,history=h,
            option_context=valid,now=now)["box_sources"]["O"]["cache_present"])
        for patch in ({"expiry":"2020-01-01"},{"expiry":"not-a-date"},
                      {"expiry":"2026-11-23T00:00:00"},{"expiry":""},
                      {"expiry":None},{"expiry":True},
                      {"symbol":"BANKNIFTY"},{"signal_eligible":True}):
            with self.subTest(patch=patch):
                x=four_box_source_readiness(
                    symbol="NIFTY",timeframe="1m",generation=3,history=h,
                    option_context=dict(valid,**patch),now=now)
                self.assertFalse(x["box_sources"]["O"]["cache_present"])
                self.assertEqual(x["box_sources"]["O"]["blocker"],
                                 "MATCHING_DHAN_OPTION_EXPIRY_CONTEXT_MISSING")
                self.assertEqual(x["live_vote_count"],0)
                self.assertEqual(x["provider_requests"],0)
                self.assertEqual(x["orders_sent"],0)

    def test_real_cached_all_doji_is_wait_not_bearish(self):
        h=history()
        for row in h["bars"][-8:]:
            row[4]=row[1]
        x=four_box_source_readiness(
            symbol="NIFTY",timeframe="1m",generation=3,history=h,
            now=h["bars"][-1][0]+60)
        self.assertIsNone(x["box_sources"]["C"]["historical_bullish"])
        self.assertEqual(x["box_sources"]["C"]["blocker"],
                         "HIST_CANDLE_DIRECTION_OR_SPACING_NOT_READY")
        self.assertEqual(x["live_vote_count"],0)

    def test_doctor_bridges_both_paths_without_adding_provider_requests(self):
        text=(ROOT/"src"/"main.py").read_text()
        self.assertIn('"four_box_source_readiness":four_box_readiness',text)
        self.assertIn('"four_box_source_readiness":master_four_box_readiness',text)
        self.assertIn('from v3_four_box_source_readiness import four_box_source_readiness',text)


if __name__=="__main__":
    unittest.main()
