"""Joint 18-filter × five-engine HIST regression; synthetic OHLCV test fixture ONLY.

No broker requests, no market-live claims, no Oracle deployment and no orders.
This is one gate across all source lanes, not 18 independent data engines.
"""
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from scanner_engine import ALL_FILTERS, OPTION_FILTERS, analyze
from filter_wiring_audit import CANDLE_FILTERS, filter_wiring_matrix
from five_engine import ENGINE_NAMES
from v3_historical_vote_replay import historical_vote_replay

IST=timezone(timedelta(hours=5,minutes=30))


def completed_fixture(timeframe):
    seconds={"1m":60,"3m":180,"5m":300}[timeframe]
    start=int(datetime(2026,11,23,9,15,tzinfo=IST).timestamp())
    bars=[]
    for i in range(60):
        p=25000 + (i//4)*2 + (i%4)*0.25
        bars.append([start+i*seconds,p,p+2,p-2,p+1 if i%3 else p-1,100+i])
    return bars


class JointFiveBoxesEighteenFilters(unittest.TestCase):
    def test_canonical_eighteen_registry_and_exact_five_lanes(self):
        self.assertEqual(len(ALL_FILTERS),18)
        self.assertEqual(len(set(ALL_FILTERS)),18)
        self.assertEqual(len(CANDLE_FILTERS),13)
        self.assertEqual(len(OPTION_FILTERS),4)
        self.assertEqual(set(ALL_FILTERS)-set(CANDLE_FILTERS)-set(OPTION_FILTERS),
                         {"News Headlines"})
        self.assertEqual(ENGINE_NAMES,
                         ("technical","candle","news","futures","options"))

    def test_all_eighteen_scanner_filters_and_five_boxes_each_frame(self):
        for frame,seconds in (("1m",60),("3m",180),("5m",300)):
            with self.subTest(timeframe=frame):
                bars=completed_fixture(frame)
                before=[b[:] for b in bars]
                scan=analyze(bars,selected=list(ALL_FILTERS),timeframe=frame)
                self.assertEqual(scan["count"],60)
                self.assertEqual(scan["timestamp"],bars[-1][0])
                self.assertEqual(set(v["name"] for v in scan["votes"]),set(ALL_FILTERS))
                self.assertTrue(all(
                    row["vote"] is None for row in scan["votes"]
                    if row["name"] in OPTION_FILTERS or row["name"]=="News Headlines"))
                wire=filter_wiring_matrix(
                    ALL_FILTERS,scan["votes"],source="Dhan",
                    timeframe=frame,candle_ready=True,
                    options_context=False,news_context=False)
                self.assertEqual(len(wire),18)
                self.assertTrue(all(
                    row["state"] in ("OPTION_DATA_MISSING","NEWS_DATA_MISSING")
                    for row in wire if row["name"] in OPTION_FILTERS
                    or row["name"]=="News Headlines"))
                replay=historical_vote_replay(
                    symbol="NIFTY",timeframe=frame,generation=7,
                    source="Dhan",bars=bars,filter_rows=scan["votes"],
                    history_timestamp=bars[-1][0]+seconds)
                self.assertEqual([box["engine"] for box in replay["boxes"]],
                                 list(ENGINE_NAMES))
                self.assertEqual([box["state"] for box in replay["boxes"]][2:],
                                 ["WAIT","WAIT","WAIT"])
                self.assertEqual(replay["boxes"][0]["state"],"HIST_VOTE")
                self.assertEqual(replay["boxes"][1]["state"],"HIST_VOTE")
                self.assertEqual(replay["combined"]["state"],"WAIT")
                self.assertEqual(replay["combined"]["coverage"],2)
                self.assertEqual(replay["provider_requests"],0)
                self.assertEqual(replay["orders_sent"],0)
                self.assertFalse(replay["verified_live"])
                self.assertEqual(bars,before)

    def test_no_legacy_context_can_promote_news_futures_options(self):
        bars=completed_fixture("1m")
        raw=analyze(bars,selected=ALL_FILTERS,timeframe="1m")
        contaminated=[
            dict(row,vote=1) if row["name"] in OPTION_FILTERS
            or row["name"]=="News Headlines" else dict(row)
            for row in raw["votes"]]
        clean=historical_vote_replay(
            symbol="NIFTY",timeframe="1m",generation=7,source="Dhan",
            bars=bars,filter_rows=raw["votes"],history_timestamp=bars[-1][0]+60)
        polluted=historical_vote_replay(
            symbol="NIFTY",timeframe="1m",generation=7,source="Dhan",
            bars=bars,filter_rows=contaminated,
            history_timestamp=bars[-1][0]+60)
        self.assertEqual(polluted["technical_vote"],clean["technical_vote"])
        self.assertEqual([x["state"] for x in polluted["boxes"]][2:],
                         ["WAIT","WAIT","WAIT"])
        self.assertFalse(polluted["verified_live"])
        self.assertEqual(polluted["orders_sent"],0)


if __name__=="__main__":
    unittest.main()
