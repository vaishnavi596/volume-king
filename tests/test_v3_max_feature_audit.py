"""Full phone Doctor feature audit: news RSS, PCR, Max Pain, OI, Oracle WAIT."""
import unittest
from v3_max_feature_audit import audit_features
from v3_stock_diagnostics import classify_stock

def run(news=None,metrics=None,assess=None):
    return audit_features(news_cache=news or {},option_metrics=metrics or {},
          assessment_cache=assess or {},selected_symbol="NIFTY",
          selected_expiry="2026-11-23",generation=2,
          scanner_symbol="NIFTY",scanner_timeframe="1m",
          active_filters=["Supertrend","EMA 9/21"],now=1795300000)

class TestMaximumFeatureAudit(unittest.TestCase):
    def test_missing_news_and_chain_give_distinct_codes(self):
        x=run()["features"]
        self.assertEqual(x["news_global"]["code"],"NEWS_CACHE_EMPTY")
        self.assertEqual(x["news_sentiment_vote"]["state"],"NOT_CONNECTED")
        self.assertEqual(x["pcr"]["code"],"OPTION_CHAIN_CONTEXT_MISSING")
        self.assertEqual(x["max_pain"]["code"],"OPTION_CHAIN_CONTEXT_MISSING")
        self.assertEqual(x["oi_support"]["state"],"UNAVAILABLE")
        self.assertFalse(run()["all_features_live_ready"])

    def test_valid_cached_news_is_context_not_direction_vote(self):
        news={"GLOBAL":{"items":[{"title":"Markets climb","published":1795299900}],
                        "source":"BBC News Business","status":"Available"}}
        d=run(news=news)["features"]
        self.assertEqual(d["news_global"]["state"],"AVAILABLE_CONTEXT")
        self.assertEqual(d["news_global"]["count"],1)
        self.assertFalse(d["news_global"]["directional_vote"])
        self.assertEqual(d["news_sentiment_vote"]["code"],"NEWS_DIRECTIONAL_ENGINE_UNVERIFIED")

    def test_option_metrics_valid_but_unverified_and_expiry_scoped(self):
        x=run(metrics={"source":"dhan","symbol":"NIFTY","expiry":"2026-11-23",
                 "freshness":"unverified","signal_eligible":False,
                 "pcr":1.15,"max_pain":24000})["features"]
        self.assertEqual(x["pcr"]["value"],1.15)
        self.assertEqual(x["max_pain"]["value"],24000)
        self.assertEqual(x["pcr"]["state"],"UNVERIFIED")
        self.assertEqual(x["oi_support"]["code"],"OI_DIRECTIONAL_EVIDENCE_NOT_WIRED")
        x=run(metrics={"source":"dhan","symbol":"BANKNIFTY","expiry":"2026-11-23",
                 "freshness":"unverified","signal_eligible":False,"pcr":1.2,"max_pain":24000})["features"]
        self.assertEqual(x["pcr"]["code"],"OPTION_CHAIN_CONTEXT_MISSING")

    def test_same_expiry_unverified_provenance_is_not_missing_chain(self):
        x=run(metrics={"symbol":"NIFTY","expiry":"2026-11-23",
                       "source":"unknown","freshness":"unverified",
                       "signal_eligible":False,"pcr":1.1,"max_pain":24000})["features"]
        for key in ("pcr","max_pain","oi_support","oi_resistance"):
            self.assertEqual(x[key]["state"],"UNVERIFIED")
            self.assertEqual(x[key]["code"],"OPTION_CHAIN_PROVENANCE_UNVERIFIED")
            self.assertFalse(x[key]["directional_vote"])

    def test_bad_pcr_nan_and_future_news_are_not_available(self):
        bad={"source":"dhan","symbol":"NIFTY","expiry":"2026-11-23",
             "freshness":"unverified","signal_eligible":False,"pcr":float("nan"),"max_pain":0}
        x=run(metrics=bad)["features"]
        self.assertEqual(x["pcr"]["code"],"DHAN_METRIC_INVALID_OR_MISSING")
        self.assertEqual(x["max_pain"]["state"],"ERROR")
        news={"GLOBAL":{"items":[{"title":"Tomorrow","published":1795300100}],"status":"Available"}}
        self.assertEqual(run(news=news)["features"]["news_global"]["state"],"UNAVAILABLE")

    def test_oracle_five_assessment_scope_and_status(self):
        rows=[{"id":id,"status":"unavailable"} for id in
            ("oi_support","oi_resistance","max_pain","pcr","candle_trend")]
        rows[-1]["status"]="available"
        payload={"symbol":"NIFTY","source":"dhan","freshness":"unverified",
                 "signal_eligible":False,"live_orders_enabled":False,
                 "bullish_score":None,"bearish_score":None,
                 "assessment_filters":rows}
        a={(2,"NIFTY","1m","2026-11-23"):
              {"timeframe":"1m","expiry":"2026-11-23","data":payload},
           (2,"NIFTY","1m","2026-11-30"):
              {"timeframe":"1m","expiry":"2026-11-30","data":dict(payload,
                assessment_filters=[{"id":"pcr","status":"available"}])}}
        x=run(assess=a)["features"]
        self.assertEqual(x["assessment_candle_trend"]["state"],"AVAILABLE_CONTEXT")
        self.assertEqual(x["assessment_pcr"]["code"],"ASSESSMENT_EVIDENCE_NOT_AVAILABLE")
        wrong={(2,"NIFTY","1m","2026-11-30"):a[(2,"NIFTY","1m","2026-11-30")]}
        self.assertEqual(run(assess=wrong)["features"]["assessment_pcr"]["state"],"UNAVAILABLE")
        unsafe=dict(payload,signal_eligible=True)
        self.assertEqual(run(assess={(2,"NIFTY","1m","2026-11-23"):
              {"timeframe":"1m","expiry":"2026-11-23","data":unsafe}})
              ["features"]["assessment_candle_trend"]["state"],"UNAVAILABLE")

    def test_incomplete_or_duplicate_assessment_never_reports_available(self):
        base={"symbol":"NIFTY","source":"dhan","freshness":"unverified",
              "signal_eligible":False,"live_orders_enabled":False,
              "bullish_score":None,"bearish_score":None}
        good=[{"id":key,"status":"available"} for key in
              ("oi_support","oi_resistance","max_pain","pcr","candle_trend")]
        for rows in (good[:1],good[:4]+[good[0]],good[:4]+[{"id":"bogus","status":"available"}]):
            payload=dict(base,assessment_filters=rows)
            record={"timeframe":"1m","expiry":"2026-11-23","data":payload}
            features=run(assess={(2,"NIFTY","1m","2026-11-23"):record})["features"]
            for key in ("oi_support","oi_resistance","max_pain","pcr","candle_trend"):
                self.assertEqual(features["assessment_"+key]["state"],"UNAVAILABLE")
                self.assertFalse(features["assessment_"+key]["directional_vote"])

    def test_doctor_lists_all_seventeen_selected_filters(self):
        chosen=["filter_"+str(i) for i in range(17)]
        report=audit_features(news_cache={},option_metrics={},assessment_cache={},
              selected_symbol="NIFTY",selected_expiry="2026-11-23",generation=2,
              scanner_symbol="NIFTY",scanner_timeframe="1m",active_filters=chosen,
              now=1795300000)
        x=report["features"]["analysis_filter_settings"]
        self.assertEqual(x["selected_count"],17)
        self.assertEqual(x["selected_names"],chosen)

    def test_missing_optional_frames_not_fatal_for_stock(self):
        t=1795250000
        bars=[[t+i*60,100,101,99,100,50] for i in range(4)]
        hist={("NIFTY",tf,1):{"source":"Dhan","_scanner_timeframe":tf,"bars":bars}
              for tf in ("1m","3m")}
        x=classify_stock("NIFTY",{"source":"Dhan","price":100},hist,1)
        self.assertEqual(x["error_codes"],[])
        self.assertEqual(x["state"],"CACHE_PRESENT_UNVERIFIED")
        self.assertEqual(x["optional_frames_missing"],["5m","10m","15m","30m"])
        self.assertFalse(x["live_signal_eligible"])
        self.assertIn("DATA_INCOMPLETE",
                      classify_stock("NIFTY",{"source":"Dhan","price":100},hist,1,
                          required_frames=("1m","3m","5m"))["error_codes"])

if __name__=="__main__":
    unittest.main()
