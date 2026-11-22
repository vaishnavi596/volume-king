"""Render prior real completed-candle votes as HIST, never as fabricated LIVE."""
import time
import unittest
from test_audit import start

class HistoricalVoteUiTests(unittest.TestCase):
    def test_offline_technical_engine_keeps_last_valid_historical_vote(self):
        page,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        v["watch_signal_cache"]["HDFCBANK"]={
            "source":"Dhan","symbol":"HDFCBANK","timestamp":time.time()-1000,
            "historical":True,"freshness":"unverified","live_verified":False,
            "votes":[{"name":"RSI","vote":1},{"name":"MACD","vote":-1},
                     {"name":"EMA 9/21","vote":1}]}
        # No authenticated Dhan session. Cached historical evidence must not
        # disappear or claim LIVE when broker is disconnected.
        row=v["five_engine_chips"]("HDFCBANK")
        visible=[card.content.value for group in row.controls for card in group.controls
                 if hasattr(card.content,"value")]
        self.assertTrue(any("T HIST B67/S33" in label for label in visible),visible)
        self.assertTrue(any("N WAIT" in label for label in visible),visible)
        self.assertTrue(any("F WAIT" in label for label in visible),visible)
        self.assertTrue(any("O WAIT" in label for label in visible),visible)

    def test_nifty_no_bars_shows_previous_historical_votes_not_price_direction(self):
        page,v=start({"source":"Dhan","scanner_live":False,"last_page":2})
        v["watch_signal_cache"]["NIFTY"]={
            "source":"Dhan","symbol":"NIFTY","timeframe":"1m","timestamp":time.time()-1000,
            "historical":True,"freshness":"unverified","live_verified":False,
            "votes":[{"name":"RSI","vote":-1},{"name":"MACD","vote":-1}]}
        v["quotes"]["NIFTY"]={"source":"Dhan","price":25100,"change":-2.0,
                               "fetched_at":time.time(),"bars":[]}
        root=v["dashboard_market_indices"]()
        texts=[]
        def walk(control):
            if hasattr(control,"value") and isinstance(control.value,str):
                texts.append(control.value)
            for child in control._get_children():
                walk(child)
        walk(root)
        self.assertFalse(any("Bearish 100%" in t for t in texts),texts[-30:])
        self.assertTrue(any("1m historical candle votes unavailable" in t for t in texts),texts[-30:])
        # No completed 1m candles: cached indicator votes cannot substitute for candle evidence.
        # The dashboard must show a truthful WAIT rather than inventing HIST or LIVE.
        self.assertTrue(any("C WAIT" in t for t in texts),texts[-30:])
        self.assertFalse(any(t=="LIVE" for t in texts),texts[-30:])
