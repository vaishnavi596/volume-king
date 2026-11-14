"""Batch 4 five-engine directional evidence must fail closed on missing inputs."""
import unittest
from five_engine import option_from_component, news_from_headline_cues
from five_engine import ENGINE_NAMES, EngineEvidence, combine_evidence, empty_evidence, technical_from_votes, compose_snapshot, scanner_snapshot, snapshot_for_display


def evidence(name, bullish=None, verified=False):
    return EngineEvidence(name=name, bullish=bullish,
                          bearish=None if bullish is None else 100-bullish,
                          verified=verified, timestamp=1234567890 if verified else None,
                          source="dhan" if verified else "", reason="Test fixture")


class FiveEngineTests(unittest.TestCase):
    def test_missing_is_not_zero_or_bearish(self):
        missing=evidence("options")
        self.assertEqual(missing.display()["state"],"WAIT")
        self.assertIsNone(missing.display()["bullish"])
        self.assertFalse(missing.eligible)

    def test_unverified_percentage_cannot_vote(self):
        rows=[evidence(n,90,False) for n in ENGINE_NAMES]
        result=combine_evidence(rows)
        self.assertEqual(result["state"],"WAIT")
        self.assertEqual(result["coverage"],0)

    def test_three_independent_verified_engines_can_agree(self):
        rows=[evidence(n,80,True) if n in ENGINE_NAMES[:3] else evidence(n) for n in ENGINE_NAMES]
        result=combine_evidence(rows)
        self.assertEqual(result["state"],"BULLISH")
        self.assertEqual(result["coverage"],3)
        self.assertEqual(result["bullish"],80)

    def test_conflict_waits(self):
        rows=[evidence(n,v,True) for n,v in zip(ENGINE_NAMES,(80,20,80,20,50))]
        self.assertEqual(combine_evidence(rows)["state"],"WAIT")

    def test_two_verified_insufficient(self):
        rows=[evidence(n,80,True) if n in ENGINE_NAMES[:2] else evidence(n) for n in ENGINE_NAMES]
        self.assertEqual(combine_evidence(rows)["state"],"WAIT")

    def test_neutral_does_not_inflate_direction(self):
        rows=[evidence(n,v,True) for n,v in zip(ENGINE_NAMES,(50,50,80,80,50))]
        self.assertEqual(combine_evidence(rows)["state"],"WAIT")

    def test_invalid_inputs_rejected(self):
        for values in ((101,-1),(40,40),(True,False)):
            with self.subTest(values=values),self.assertRaises(ValueError):
                EngineEvidence("news",values[0],values[1],True,"",123,"dhan")
        with self.assertRaises(ValueError):
            combine_evidence([evidence("technical")]*5)


    def test_empty_snapshot_cannot_vote(self):
        snapshot=compose_snapshot()
        self.assertEqual(tuple(e.name for e in snapshot["engines"]),ENGINE_NAMES)
        self.assertEqual(snapshot["combined"]["coverage"],0)
        self.assertEqual(snapshot["combined"]["state"],"WAIT")

    def test_technical_votes_do_not_invent_live_verification(self):
        technical=technical_from_votes(["BUY","BUY","SELL","NEUTRAL"])
        self.assertEqual((technical.bullish,technical.bearish),(67,33))
        self.assertFalse(technical.eligible)
        self.assertEqual(technical.display()["state"],"WAIT")
        snapshot=compose_snapshot(technical=technical)
        self.assertEqual(snapshot["combined"]["coverage"],0)
        self.assertIsNone(snapshot["engines"][4].bullish)

    def test_verified_technical_does_not_fill_candle_news_or_derivatives(self):
        technical=technical_from_votes(["BUY","SELL","BUY"],verified=True,
                                        timestamp=1234567890,source="dhan")
        snapshot=compose_snapshot(technical=technical)
        self.assertTrue(snapshot["engines"][0].eligible)
        self.assertEqual(snapshot["combined"]["coverage"],1)
        self.assertEqual(snapshot["combined"]["state"],"WAIT")
        self.assertTrue(all(not row.eligible for row in snapshot["engines"][1:]))

    def test_engine_identity_cannot_be_swapped(self):
        with self.assertRaises(ValueError):
            compose_snapshot(technical=evidence("news",80,True))


    def test_scanner_adapter_reuses_votes_without_double_counting(self):
        scan={"votes":[{"name":"Filter 1","vote":1},{"name":"Filter 2","vote":-1},{"name":"Filter 3","vote":1},{"name":"Filter 4","vote":0}],
              "source":"Dhan","timestamp":1234567890,
              "freshness":"historical_unverified","historical":True,"live_verified":False}
        result=scanner_snapshot(scan)
        self.assertEqual((result["engines"][0].bullish,result["engines"][0].bearish),(67,33))
        self.assertEqual(result["combined"]["state"],"WAIT")
        self.assertEqual(result["combined"]["coverage"],0)
        self.assertTrue(all(e.bullish is None for e in result["engines"][1:]))

    def test_scanner_adapter_requires_explicit_verified_dhan(self):
        scan={"votes":[{"name":"Filter 5","vote":1},{"name":"Filter 6","vote":1},{"name":"Filter 7","vote":-1}], "source":"Dhan",
              "timestamp":1234567890,"freshness":"verified_live",
              "historical":False,"live_verified":True}
        result=scanner_snapshot(scan)
        self.assertEqual(result["combined"]["coverage"],1)
        self.assertEqual(result["combined"]["state"],"WAIT")
        scan["source"]="Yahoo Finance"
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],0)

    def test_scanner_adapter_rejects_boolean_votes(self):
        result=scanner_snapshot({"votes":[{"name":"Filter 8","vote":True},{"name":"Filter 9","vote":False}]})
        self.assertEqual(result["combined"]["coverage"],0)


    def test_cached_verified_signal_expires_at_render_time(self):
        rows=[EngineEvidence(n,80,20,verified=True,timestamp=1234567890,source="Dhan") for n in ENGINE_NAMES]
        snap=compose_snapshot(**dict(zip(ENGINE_NAMES,rows)))
        self.assertEqual(snapshot_for_display(snap,now=1234567900)["combined"]["state"],"BULLISH")
        stale=snapshot_for_display(snap,now=1234569000)
        self.assertEqual(stale["combined"]["state"],"WAIT")
        self.assertEqual(stale["combined"]["coverage"],0)
        self.assertTrue(all(e.display()["state"]=="WAIT" for e in stale["engines"]))

    def test_future_timestamp_does_not_count_as_live(self):
        rows=[EngineEvidence(n,80,20,verified=True,timestamp=1234567890,source="Dhan") for n in ENGINE_NAMES]
        snap=compose_snapshot(**dict(zip(ENGINE_NAMES,rows)))
        self.assertEqual(snapshot_for_display(snap,now=1234567000)["combined"]["coverage"],0)

    def test_malformed_snapshot_fails_closed(self):
        self.assertEqual(snapshot_for_display({},now=1234567890)["combined"]["state"],"WAIT")


    def test_provider_switch_never_promotes_old_evidence(self):
        old=EngineEvidence("technical",80,20,verified=True,
                           timestamp=1234567890,source="Yahoo Finance")
        snap=compose_snapshot(technical=old)
        shown=snapshot_for_display(snap,now=1234567900)
        self.assertEqual(shown["combined"]["coverage"],0)
        self.assertEqual(shown["engines"][0].display()["state"],"WAIT")
        self.assertIn("source mismatch",shown["engines"][0].reason)

    def test_matching_dhan_evidence_remains_eligible(self):
        live=EngineEvidence("technical",80,20,verified=True,
                            timestamp=1234567890,source="Dhan")
        shown=snapshot_for_display(compose_snapshot(technical=live),now=1234567900)
        self.assertEqual(shown["combined"]["coverage"],1)
        self.assertEqual(shown["combined"]["state"],"WAIT")


    def test_malformed_vote_container_fails_closed(self):
        for bad in ("BUY", {"name":"Filter 10","vote":1}, 123):
            with self.subTest(bad=bad):
                snap=scanner_snapshot({"votes":bad,"source":"Dhan",
                                       "timestamp":1234567890,"live_verified":True,
                                       "freshness":"verified_live","historical":False})
                self.assertEqual(snap["combined"]["coverage"],0)

    def test_missing_or_invalid_scanner_timestamp_fails_closed(self):
        for bad in (None,0,-1,True,float("nan"),float("inf"),"1234567890"):
            with self.subTest(bad=bad):
                snap=scanner_snapshot({"votes":[{"name":"Filter 11","vote":1}],
                                       "timestamp":bad,"source":"Dhan",
                                       "live_verified":True,"freshness":"verified_live",
                                       "historical":False})
                self.assertEqual(snap["combined"]["coverage"],0)
                self.assertEqual(snap["engines"][0].display()["state"],"WAIT")


    def test_snapshot_rejects_malformed_or_misassigned_engine(self):
        with self.assertRaises(ValueError):
            compose_snapshot(technical={"bullish":80,"bearish":20})
        with self.assertRaises(ValueError):
            compose_snapshot(technical=EngineEvidence("options",80,20))
        with self.assertRaises(ValueError):
            compose_snapshot(candle=object())


    def test_scanner_malformed_votes_fail_closed(self):
        for bad in ("BUY",{"name":"Filter 12","vote":1},42,True):
            with self.subTest(bad=bad):
                snap=scanner_snapshot({"votes":bad,"source":"Dhan",
                    "freshness":"verified_live","live_verified":True,
                    "historical":False,"timestamp":1234567890})
                self.assertEqual(snap["combined"]["coverage"],0)
                self.assertEqual(snap["engines"][0].display()["state"],"WAIT")


    def test_single_vote_cannot_claim_100_percent_technical_strength(self):
        for votes in (["BUY"],["SELL","SELL"],["BUY","NEUTRAL"]):
            with self.subTest(votes=votes):
                row=technical_from_votes(votes,timestamp=1234567890,source="Dhan",verified=True)
                self.assertFalse(row.eligible)
                self.assertEqual(row.display()["state"],"WAIT")
        row=technical_from_votes(["BUY","BUY","SELL"],timestamp=1234567890,
                                 source="Dhan",verified=True)
        self.assertEqual(row.display()["bullish"],67)


    def test_scanner_mixed_malformed_votes_fail_closed(self):
        snap=scanner_snapshot({"votes":[{"name":"Filter 13","vote":1},{"name":"Filter 14","vote":1},{"name":"Filter 15","vote":-1},None],
            "source":"Dhan","timestamp":1234567890,"freshness":"verified_live",
            "live_verified":True,"historical":False})
        self.assertEqual(snap["combined"]["coverage"],0)
        self.assertEqual(snap["engines"][0].display()["state"],"WAIT")


    def test_scanner_invalid_vote_values_fail_closed(self):
        for invalid in (True,False,2,-2,"BUY",None,1.0):
            with self.subTest(invalid=invalid):
                snap=scanner_snapshot({"votes":[{"name":"Filter 16","vote":1},{"name":"Filter 17","vote":-1},
                    {"name":"Filter 18","vote":1},{"name":"Filter 19","vote":invalid}],"source":"Dhan",
                    "timestamp":1234567890,"freshness":"verified_live",
                    "live_verified":True,"historical":False})
                self.assertEqual(snap["combined"]["coverage"],0)


    def test_duplicate_filter_votes_cannot_inflate_technical_strength(self):
        scan={"votes":[{"name":"RSI 14","vote":1},{"name":"RSI 14","vote":1},
                       {"name":"MACD","vote":-1}],
              "source":"Dhan","timestamp":1234567890,"freshness":"verified_live",
              "live_verified":True,"historical":False}
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],0)
        scan["votes"][1]["name"]="EMA 9/21"
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],1)


    def test_filter_name_whitespace_and_case_cannot_duplicate_votes(self):
        scan={"votes":[{"name":"RSI 14","vote":1},
                       {"name":" rsi 14 ","vote":1},
                       {"name":"MACD","vote":-1}],
              "source":"Dhan","timestamp":1234567890,
              "freshness":"verified_live","live_verified":True,"historical":False}
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],0)


    def test_option_component_requires_measured_directional_strength(self):
        for component in (None, {}, {"available":True,"source":"Dhan",
            "verified":True,"direction_basis":"validated_trade_flow",
            "bias":"BULLISH","timestamp":1234567890}):
            row=option_from_component(component)
            self.assertEqual(row.display()["state"],"WAIT")
            self.assertIsNone(row.bullish)

if __name__=="__main__":unittest.main()


def test_news_headline_keywords_never_count_as_verified_market_direction():
    for cue in (None, {}, {"bias":"POSITIVE","positive":5,"negative":0},
                {"bias":"NEGATIVE","positive":0,"negative":8}):
        evidence=news_from_headline_cues(cue)
        assert evidence.name=="news"
        assert evidence.display()["state"]=="WAIT"
        assert evidence.bullish is None and evidence.bearish is None


def test_verified_evidence_rejects_blank_or_non_string_source():
    for source in ("", "   ", None, 123, True):
        row = EngineEvidence("technical", 80, 20, verified=True,
                             timestamp=1234567890, source=source)
        assert not row.eligible
        assert row.display()["state"] == "WAIT"
        assert combine_evidence([row] + [EngineEvidence(n) for n in ENGINE_NAMES[1:]])["coverage"] == 0


def test_verified_flag_must_be_boolean_true_not_truthy():
    for flag in (1, "yes", [True], {"verified": True}):
        row = EngineEvidence("technical", 80, 20, verified=flag,
                             timestamp=1234567890, source="Dhan")
        assert row.eligible is False
        assert row.display()["state"] == "WAIT"
    assert EngineEvidence("technical", 80, 20, verified=True,
                          timestamp=1234567890, source="Dhan").eligible is True
