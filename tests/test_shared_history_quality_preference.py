"""A newer partial index response cannot supersede a complete old 5m history."""
import time
import unittest
from test_audit import start

def bars(start,count):
    return [[start+300*i,100.0,102.0,99.0,101.0,1000.0] for i in range(count)]

class SharedHistoryQualitySelectionTests(unittest.TestCase):
    def test_nifty_prefers_40_good_quote_bars_to_newer_four_chart_bars(self):
        page,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        generation=v["provider_generation"][0]
        now=int(time.time())-300*45
        old=bars(now,40)
        partial=bars(now+300*40,4)
        v["quotes"]["NIFTY"]={"source":"Dhan","bars":old,
                                "candle_fetched_at":time.time()-80}
        v["chart_snapshots"][("NIFTY","5m",generation)]={
            "source":"Dhan","bars":partial,"candle_fetched_at":time.time()}
        chosen=v["shared_history"]("NIFTY")
        self.assertEqual(chosen["bars"],old)

    def test_newer_full_history_supersedes_old_full_history(self):
        page,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        generation=v["provider_generation"][0]
        now=int(time.time())-300*45
        old=bars(now,40)
        newer=bars(now+300,40)
        v["quotes"]["NIFTY"]={"source":"Dhan","bars":old}
        v["chart_snapshots"][("NIFTY","5m",generation)]={
            "source":"Dhan","bars":newer,"candle_fetched_at":time.time()}
        self.assertEqual(v["shared_history"]("NIFTY")["bars"],newer)

    def test_other_provider_history_cannot_win(self):
        page,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        generation=v["provider_generation"][0]
        now=int(time.time())-300*45
        old=bars(now,40)
        v["quotes"]["NIFTY"]={"source":"Dhan","bars":old}
        v["chart_snapshots"][("NIFTY","5m",generation)]={
            "source":"Yahoo Finance","bars":bars(now+300,40)}
        self.assertEqual(v["shared_history"]("NIFTY")["bars"],old)
