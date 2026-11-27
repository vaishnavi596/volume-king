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
    def test_measured_dhan_derivative_adapters_only_accept_proven_strength(self):
        from five_engine import futures_from_component
        valid={"source":"Dhan","verified":True,"contract":"NIFTY-FUT",
               "direction_basis":"validated_trade_flow","timestamp":1234567890,
               "bullish":72,"bearish":28}
        future=futures_from_component(valid)
        self.assertTrue(future.eligible)
        self.assertEqual(future.display()["state"],"BULLISH")
        option=option_from_component(dict(valid,available=True,bias="BULLISH"))
        self.assertTrue(option.eligible)
        for field,bad in (("bullish",True),("bearish",27),
                          ("direction_basis","oi_inference"),("source","Yahoo Finance")):
            with self.subTest(field=field):
                broken=dict(valid,available=True,bias="BULLISH",**{field:bad})
                self.assertFalse(futures_from_component(broken).eligible)
                self.assertFalse(option_from_component(broken).eligible)
        self.assertFalse(option_from_component(dict(valid,available=True,bias="BULLISH",
                                                    bullish=None)).eligible)

    def test_independent_five_adapter_fusion_respects_three_engine_quorum(self):
        from five_engine import compose_verified_adapter_snapshot
        scan={"votes":[{"name":"EMA 9/21","vote":1},
                       {"name":"RSI 14","vote":1},
                       {"name":"MACD","vote":1}],
              "source":"Dhan","timestamp":1234567890,
              "freshness":"verified_live","historical":False,"live_verified":True}
        candle=EngineEvidence("candle",80,20,verified=True,
                              timestamp=1234567890,source="Dhan")
        news=EngineEvidence("news",75,25,verified=True,
                            timestamp=1234567890,source="Dhan")
        incomplete=compose_verified_adapter_snapshot(scan,candle=candle,
                                                       now=1234567900)
        self.assertEqual(incomplete["combined"]["coverage"],2)
        self.assertEqual(incomplete["combined"]["state"],"WAIT")
        complete=compose_verified_adapter_snapshot(scan,candle=candle,news=news,
                                                     now=1234567900)
        self.assertEqual(complete["combined"]["coverage"],3)
        self.assertEqual(complete["combined"]["state"],"BULLISH")
        self.assertFalse(complete["engines"][3].eligible)
        self.assertFalse(complete["engines"][4].eligible)
        stale=compose_verified_adapter_snapshot(scan,candle=candle,news=news,
                                                 now=1234569000)
        self.assertEqual(stale["combined"]["coverage"],0)
        self.assertEqual(stale["combined"]["state"],"WAIT")

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
        scan={"votes":[{"name":"EMA 9/21","vote":1},{"name":"RSI 14","vote":-1},{"name":"MACD","vote":1},{"name":"Supertrend","vote":0}],
              "source":"Dhan","timestamp":1234567890,
              "freshness":"historical_unverified","historical":True,"live_verified":False}
        result=scanner_snapshot(scan)
        self.assertEqual((result["engines"][0].bullish,result["engines"][0].bearish),(67,33))
        self.assertEqual(result["combined"]["state"],"WAIT")
        self.assertEqual(result["combined"]["coverage"],0)
        self.assertTrue(all(e.bullish is None for e in result["engines"][1:]))

    def test_seventeen_selected_filters_keep_technical_engine_when_oi_waits(self):
        selected = ["Supertrend", "EMA 9/21", "RSI 14", "MACD", "VWAP",
                    "SMC Structure", "Order Block", "Pivot Points", "FVG",
                    "Liquidity Sweep", "OI Support", "OI Resistance",
                    "OI Profile", "Dhan Max Pain", "SMA 5/20", "Volume", "ATR 14"]
        rows = [{"name": name, "vote": (1 if i < 3 else 0), "detail": "computed"}
                for i, name in enumerate(selected)]
        for row in rows:
            if row["name"].startswith("OI ") or row["name"] == "Dhan Max Pain":
                row.update(vote=None, detail="No matching Dhan expiry snapshot; WAIT")
        scan = {"votes": rows, "source": "Dhan", "timestamp": 1234567890,
                "freshness": "verified_live", "historical": False, "live_verified": True}
        snapshot = scanner_snapshot(scan)
        technical = snapshot["engines"][0]
        self.assertTrue(technical.eligible)
        self.assertEqual((technical.bullish, technical.bearish), (100, 0))
        self.assertEqual(snapshot["combined"]["coverage"], 1)
        self.assertEqual(snapshot["combined"]["state"], "WAIT")
        self.assertTrue(all(not engine.eligible for engine in snapshot["engines"][1:]))

    def test_unavailable_known_context_cannot_turn_into_directional_votes(self):
        base = [{"name": "Supertrend", "vote": 1},
                {"name": "EMA 9/21", "vote": 1},
                {"name": "RSI 14", "vote": -1}]
        for name in ("OI Support", "OI Resistance", "OI Profile", "Dhan Max Pain",
                     "News Headlines", "VWAP", "Volume"):
            with self.subTest(name=name):
                rows = base + [{"name": name, "vote": None,
                                "detail": "Informational Dhan context"}]
                snapshot = scanner_snapshot({
                    "votes": rows, "source": "Dhan", "timestamp": 1234567890,
                    "freshness": "verified_live", "historical": False,
                    "live_verified": True})
                self.assertEqual(snapshot["combined"]["coverage"], 1)
                self.assertEqual(snapshot["engines"][0].bullish, 67)
                self.assertTrue(all(not engine.eligible for engine in snapshot["engines"][1:]))

    def test_unknown_filter_cannot_supply_technical_evidence(self):
        scan={"votes":[{"name":"EMA 9/21","vote":1},
                       {"name":"RSI 14","vote":1},
                       {"name":"Unknown plugin","vote":1}],
              "source":"Dhan","timestamp":1234567890,
              "freshness":"verified_live","historical":False,"live_verified":True}
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],0)
        scan["votes"][2]["name"]="MACD"
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],1)

    def test_context_aliases_cannot_inflate_technical_quorum(self):
        for name in (" oi support ", "OI resistance", "oi PROFILE",
                     " dhan max pain ", "Max Pain", " NEWS HEADLINES "):
            with self.subTest(name=name):
                scan={"votes":[{"name":"RSI 14","vote":1},
                               {"name":"MACD","vote":1},
                               {"name":name,"vote":1}],
                      "source":"Dhan","timestamp":1234567890,
                      "freshness":"verified_live","historical":False,"live_verified":True}
                self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],0)
                scan["votes"].append({"name":"EMA 9/21","vote":-1})
                result=scanner_snapshot(scan)
                self.assertEqual(result["combined"]["coverage"],1)
                self.assertEqual(result["engines"][0].bullish,67)

    def test_scanner_adapter_requires_explicit_verified_dhan(self):
        scan={"votes":[{"name":"EMA 9/21","vote":1},{"name":"RSI 14","vote":1},{"name":"MACD","vote":-1}], "source":"Dhan",
              "timestamp":1234567890,"freshness":"verified_live",
              "historical":False,"live_verified":True}
        result=scanner_snapshot(scan)
        self.assertEqual(result["combined"]["coverage"],1)
        self.assertEqual(result["combined"]["state"],"WAIT")
        scan["source"]="Yahoo Finance"
        self.assertEqual(scanner_snapshot(scan)["combined"]["coverage"],0)

    def test_scanner_adapter_rejects_boolean_votes(self):
        result=scanner_snapshot({"votes":[{"name":"Supertrend","vote":True},{"name":"EMA 9/21","vote":False}]})
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
        for bad in ("BUY", {"name":"RSI 14","vote":1}, 123):
            with self.subTest(bad=bad):
                snap=scanner_snapshot({"votes":bad,"source":"Dhan",
                                       "timestamp":1234567890,"live_verified":True,
                                       "freshness":"verified_live","historical":False})
                self.assertEqual(snap["combined"]["coverage"],0)

    def test_missing_or_invalid_scanner_timestamp_fails_closed(self):
        for bad in (None,0,-1,True,float("nan"),float("inf"),"1234567890"):
            with self.subTest(bad=bad):
                snap=scanner_snapshot({"votes":[{"name":"MACD","vote":1}],
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
        for bad in ("BUY",{"name":"Supertrend","vote":1},42,True):
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
        snap=scanner_snapshot({"votes":[{"name":"EMA 9/21","vote":1},{"name":"RSI 14","vote":1},{"name":"MACD","vote":-1},None],
            "source":"Dhan","timestamp":1234567890,"freshness":"verified_live",
            "live_verified":True,"historical":False})
        self.assertEqual(snap["combined"]["coverage"],0)
        self.assertEqual(snap["engines"][0].display()["state"],"WAIT")


    def test_scanner_invalid_vote_values_fail_closed(self):
        for invalid in (True,False,2,-2,"BUY",None,1.0):
            with self.subTest(invalid=invalid):
                snap=scanner_snapshot({"votes":[{"name":"Supertrend","vote":1},{"name":"EMA 9/21","vote":-1},
                    {"name":"RSI 14","vote":1},{"name":"MACD","vote":invalid}],"source":"Dhan",
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


def test_combined_signal_rejects_non_dhan_verified_sources():
    rows = [EngineEvidence(n, 80, 20, verified=True,
                           timestamp=1234567890, source="Yahoo Finance")
            for n in ENGINE_NAMES]
    result = combine_evidence(rows)
    assert result["state"] == "WAIT" and result["coverage"] == 0
    rows[0] = EngineEvidence("technical", 80, 20, verified=True,
                             timestamp=1234567890, source="Dhan")
    result = combine_evidence(rows)
    assert result["state"] == "WAIT" and result["coverage"] == 1


def test_snapshot_rejects_unverified_and_invalid_expected_source():
    row = EngineEvidence("technical", 80, 20, verified=False,
                         timestamp=1234567890, source="Dhan")
    shown = snapshot_for_display(compose_snapshot(technical=row), now=1234567900)
    assert shown["combined"]["coverage"] == 0
    assert shown["engines"][0].display()["state"] == "WAIT"
    for source in ("", "  ", None, 123):
        try:
            snapshot_for_display(compose_snapshot(), now=1234567900, expected_source=source)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid expected source accepted")


def test_render_time_rejects_expired_and_future_evidence_together():
    rows = [EngineEvidence(n, 80, 20, verified=True,
                           timestamp=1234567890 + offset, source="Dhan")
            for n, offset in zip(ENGINE_NAMES, (-301, -300, 0, 1, 301))]
    snap = compose_snapshot(**dict(zip(ENGINE_NAMES, rows)))
    shown = snapshot_for_display(snap, now=1234567890, max_age_seconds=300)
    assert shown["combined"]["coverage"] == 2
    assert shown["combined"]["state"] == "WAIT"


def test_technical_votes_reject_malformed_and_unknown_labels():
    for votes in ([True, "BUY", "BUY", "SELL"],
                  [1, "BUY", "BUY", "SELL"],
                  ["BUY", "BUY", "SELL", "BULL"],
                  ["BUY", "BUY", "SELL", None]):
        row = technical_from_votes(votes, timestamp=1234567890,
                                   source="Dhan", verified=True)
        assert row.display()["state"] == "WAIT"
        assert row.bullish is None
    valid = technical_from_votes(["BUY", "BUY", "SELL", "NEUTRAL"],
                                 timestamp=1234567890, source="Dhan", verified=True)
    assert valid.eligible and valid.bullish == 67


def test_scanner_candle_metadata_cannot_double_count_technical_evidence():
    scan = {"source": "Dhan", "timestamp": 1234567890,
            "live_verified": True, "freshness": "verified_live",
            "historical": False,
            "votes": [{"name": "trend", "vote": 1},
                      {"name": "momentum", "vote": 1},
                      {"name": "volume", "vote": -1}],
            "candle": {"bullish": 100, "bearish": 0,
                       "verified": True, "source": "Dhan"},
            "candles": [{"open": 1, "close": 2}],
            "candle_bias": "BULLISH"}
    snapshot = scanner_snapshot(scan)
    assert snapshot["engines"][0].name == "technical"
    assert snapshot["engines"][0].eligible
    assert snapshot["engines"][1].name == "candle"
    assert not snapshot["engines"][1].eligible
    assert snapshot["combined"]["coverage"] == 1
    assert snapshot["combined"]["state"] == "WAIT"


def test_scanner_duplicate_filter_names_fail_closed_even_with_casing():
    scan = {"source": "Dhan", "timestamp": 1234567890,
            "live_verified": True, "freshness": "verified_live",
            "historical": False,
            "votes": [{"name": "Trend", "vote": 1},
                      {"name": " trend ", "vote": 1},
                      {"name": "momentum", "vote": 1}]}
    snapshot = scanner_snapshot(scan)
    assert snapshot["combined"]["coverage"] == 0
    assert all(not row.eligible for row in snapshot["engines"])


def test_futures_oi_build_up_never_fabricates_directional_vote():
    from five_engine import futures_from_component
    for component in (None, {}, {"source": "Yahoo", "verified": True},
                      {"source": "Dhan", "verified": True, "contract": "NIFTY-FUT",
                       "timestamp": 1234567890, "oi_change": 1000,
                       "price_change": 2, "volume": 90000,
                       "bias": "BULLISH"},
                      {"source": "Dhan", "verified": True, "contract": "NIFTY-FUT",
                       "timestamp": 1234567890, "direction_basis": "validated_trade_flow",
                       "bias": "BULLISH"}):
        row = futures_from_component(component)
        assert row.name == "futures"
        assert row.display()["state"] == "WAIT"
        assert row.bullish is None and row.bearish is None
        assert combine_evidence(compose_snapshot(futures=row)["engines"])["coverage"] == 0


def test_news_context_requires_symbol_publisher_freshness_and_dedup():
    from five_engine import deduplicate_news_context
    now = 1234567890
    rows = [
        {"title": "Company result", "publisher": "Wire", "published_at": now - 10, "symbols": ["RELIANCE"]},
        {"title": " company result ", "publisher": "wire", "published_at": now - 10, "symbols": ["RELIANCE"]},
        {"title": "Other stock", "publisher": "Wire", "published_at": now - 10, "symbols": ["HDFCBANK"]},
        {"title": "Old", "publisher": "Wire", "published_at": now - 601, "symbols": ["RELIANCE"]},
        {"title": "Future", "publisher": "Wire", "published_at": now + 1, "symbols": ["RELIANCE"]},
        {"title": "Missing publisher", "published_at": now, "symbols": ["RELIANCE"]},
    ]
    result = deduplicate_news_context(rows, symbol="reliance", now=now)
    assert len(result) == 1 and result[0]["title"] == "Company result"
    assert news_from_headline_cues({"bias": "POSITIVE", "count": len(result)}).display()["state"] == "WAIT"


def test_news_context_deduplicates_syndicated_publishers_and_caps_size():
    from five_engine import deduplicate_news_context
    now = 1234567890
    rows = [
        {"title": "Company  Results", "publisher": "Wire A",
         "published_at": now, "symbols": ["RELIANCE"]},
        {"title": " company results ", "publisher": "Wire B",
         "published_at": now, "symbols": ["RELIANCE"]},
    ]
    rows += [{"title": "Unique story " + str(i), "publisher": "Wire",
              "published_at": now, "symbols": ["RELIANCE"]} for i in range(40)]
    result = deduplicate_news_context(rows, symbol="RELIANCE", now=now)
    assert len(result) == 20
    assert sum(x["title"].lower().startswith("company") for x in result) == 1


def test_futures_market_context_requires_verified_mapping_and_complete_fields():
    from five_engine import futures_market_context
    now = 1234567890
    base = {"source": "Dhan", "verified": True, "mapping_verified": True,
            "contract": "NIFTY FUT", "timestamp": now, "ltp": 25000.0,
            "open_interest": 1000, "volume": 500}
    result = futures_market_context(base, now=now)
    assert result["direction"] is None and result["direction_verified"] is False
    for change in ({"mapping_verified": False}, {"source": "Yahoo"},
                   {"verified": 1}, {"timestamp": now - 301},
                   {"timestamp": now + 1}, {"ltp": 0},
                   {"volume": -1}, {"open_interest": None},
                   {"contract": "  "}):
        row = dict(base, **change)
        assert futures_market_context(row, now=now) is None


def test_futures_contract_resolver_requires_unique_verified_master_record():
    from datetime import date
    from five_engine import resolve_verified_futures_contract
    expiry = date(2026, 11, 26)
    row = {"source": "Dhan", "master_verified": True, "instrument_type": "FUT",
           "exchange_segment": "NSE_FNO", "underlying": "NIFTY",
           "expiry": "2026-11-26", "security_id": "12345", "contract": "NIFTY NOV FUT"}
    result = resolve_verified_futures_contract([row], symbol="NIFTY", expiry=expiry)
    assert result["security_id"] == "12345" and result["mapping_verified"] is True
    for patch in ({"source": "Yahoo"}, {"master_verified": 1},
                  {"instrument_type": "OPT"}, {"exchange_segment": "NSE_EQ"},
                  {"expiry": "2026-12-31"}, {"security_id": "-1"},
                  {"security_id": 12345}, {"underlying": "BANKNIFTY"}):
        assert resolve_verified_futures_contract([dict(row, **patch)], symbol="NIFTY", expiry=expiry) is None
    assert resolve_verified_futures_contract([row, row], symbol="NIFTY", expiry=expiry) is None
    assert resolve_verified_futures_contract([], symbol="NIFTY", expiry=expiry) is None


def test_batch4_listed_atm_window_seven_strikes_and_fail_closed():
    from backend.dhan_option_metrics import listed_atm_window, OptionMetricsUnavailable
    import pytest
    chain = {str(k): {"ce": {"oi": 100, "volume": 25, "last_price": 12.5},
                      "pe": {"oi": 150, "volume": 30, "last_price": 13.5}}
             for k in range(90, 111, 2)}
    payload = {"status": "success", "data": {"oc": chain}}
    out = listed_atm_window(payload, spot=100)
    assert out["atm"] == 100 and len(out["rows"]) == 7
    assert [row["strike"] for row in out["rows"]] == [94, 96, 98, 100, 102, 104, 106]
    assert out["signal_eligible"] is False and out["freshness"] == "unverified"
    assert out["rows"][3]["ce"]["volume"] == 25
    for invalid in ({"status": "error", "data": {"oc": chain}},
                    {"status": "success", "data": {"oc": dict(list(chain.items())[:6])}},
                    {"status": "success", "data": {"oc": {**chain, "100.0": chain["100"]}}}):
        with pytest.raises(OptionMetricsUnavailable):
            listed_atm_window(invalid, spot=100)
    with pytest.raises(OptionMetricsUnavailable):
        listed_atm_window(payload, spot=90)
    bad = {key: dict(value) for key, value in chain.items()}
    bad["100"] = {"ce": {"oi": -1}, "pe": {"oi": 10}}
    with pytest.raises(OptionMetricsUnavailable):
        listed_atm_window({"status": "success", "data": {"oc": bad}}, spot=100)


def test_batch4_option_window_backend_and_client_fail_closed_contract():
    from pathlib import Path
    server = Path("backend/server.py").read_text(encoding="utf-8")
    client = Path("src/server_feed.py").read_text(encoding="utf-8")
    assert "listed_atm_window(raw, spot=underlying_spot)" in server
    assert '"atm_window": window' in server
    assert 'window.get("signal_eligible") is not False' in client
    assert 'window.get("freshness") != "unverified"' in client
    assert 'window.get("atm") != strikes[3]' in client


def test_batch4_atm_window_optional_premium_volume_and_oi_are_fail_closed():
    import pytest
    from backend.dhan_option_metrics import listed_atm_window, OptionMetricsUnavailable
    chain = {str(k): {"ce": {"oi": 20, "volume": 5, "last_price": 8.0, "previous_oi": 18},
                      "pe": {"oi": 30, "volume": 6, "last_price": 9.0, "previous_oi": 25}}
             for k in range(90, 111, 2)}
    payload = {"status": "success", "data": {"oc": chain}}
    window = listed_atm_window(payload, spot=100)
    assert window["rows"][3]["ce"]["previous_oi"] == 18
    assert window["rows"][3]["pe"]["last_price"] == 9
    assert window["signal_eligible"] is False
    for field, bad_value in (("volume", -1), ("last_price", float("nan")),
                             ("previous_oi", True), ("volume", float("inf"))):
        damaged = {key: {"ce": dict(value["ce"]), "pe": dict(value["pe"])}
                   for key, value in chain.items()}
        damaged["100"]["ce"][field] = bad_value
        with pytest.raises(OptionMetricsUnavailable):
            listed_atm_window({"status": "success", "data": {"oc": damaged}}, spot=100)
    without_optional = {key: {"ce": {"oi": 20}, "pe": {"oi": 30}}
                        for key in chain}
    safe = listed_atm_window({"status": "success", "data": {"oc": without_optional}}, spot=100)
    assert "last_price" not in safe["rows"][3]["ce"]
    assert safe["freshness"] == "unverified"


def test_batch4_option_context_is_nonvoting_and_rejects_bad_rows():
    from src.five_engine import option_chain_display_context
    rows = [{"strike": float(k), "ce": {"oi": 10, "volume": 2},
             "pe": {"oi": 20, "last_price": 5.5}} for k in range(94, 107, 2)]
    payload = {"source": "dhan", "freshness": "unverified", "signal_eligible": False,
               "atm_window": {"source": "dhan", "freshness": "unverified",
                              "signal_eligible": False, "atm": 100.0, "rows": rows}}
    result = option_chain_display_context(payload)
    assert result["available"] is True and result["direction"] == "WAIT"
    assert result["signal_eligible"] is False and len(result["rows"]) == 7
    assert option_chain_display_context({**payload, "signal_eligible": True})["available"] is False
    malformed = dict(payload, atm_window=dict(payload["atm_window"], atm=102.0))
    assert option_chain_display_context(malformed)["available"] is False
    broken = [dict(row) for row in rows]
    broken[3] = dict(broken[3], ce={"oi": float("nan")})
    assert option_chain_display_context(dict(payload, atm_window=dict(payload["atm_window"], rows=broken)))["available"] is False


def test_batch4_shared_snapshot_option_context_does_not_vote():
    from src.five_engine import compose_snapshot, compose_snapshot_with_option_context
    base = compose_snapshot()
    wrapped = compose_snapshot_with_option_context(option_metrics={"source": "dhan",
        "freshness": "unverified", "signal_eligible": False})
    assert wrapped["combined"] == base["combined"]
    assert wrapped["engines"] == base["engines"]
    assert wrapped["option_context"]["available"] is False
    assert "option_context" not in base


class ScannerFiveBoxSharedRenderingContract(unittest.TestCase):
    """Source-level regression: Scanner must mount the same five chips as other screens."""

    def test_scanner_five_engine_panel_mounts_shared_chips_and_details(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('wrap_delta_section("scanner_five"', source)
        self.assertIn('five_engine_chips(scan_symbol.value or "NIFTY",display_timeframe=scan_tf.value)', source)
        self.assertIn('five_engine_summary(scan_symbol.value or "NIFTY",display_timeframe=scan_tf.value)', source)
        self.assertIn('ft.Column([(refresh_scan_boxes() and None) or five_engine_summary(scan_symbol.value or "NIFTY",display_timeframe=scan_tf.value),canonical_live_final_note(scan_symbol.value or "NIFTY",scan_tf.value),scanner_historical_final_vote()]', source)
        self.assertIn('def scanner_historical_final_vote(symbol=None, timeframe=None):', source)

    def test_shared_chips_keep_five_engine_order_and_sixth_inert(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        start = source.index("    def five_engine_chips(sym, display_timeframe=None):")
        end = source.index("    def ", start + 5)
        function = source[start:end]
        self.assertIn('("technical","T"),("candle","C"),("news","N")', function)
        self.assertIn('("futures","F"),("options","O")', function)
        self.assertIn('ft.Text("6  —"', function)
        self.assertIn('cards.append(', function)


class FiveEngineTimeframeIsolationContract(unittest.TestCase):
    def test_watchlist_chips_request_three_minute_history(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('five_cell=ft.Container(content=ft.Column([', source)
        self.assertIn('five.content=ft.Column([', source)
        self.assertIn('five_engine_chips(sym,display_timeframe="1m")', source)
        self.assertIn('scanner_historical_final_vote(sym,"1m")', source)
        self.assertIn('(display_timeframe is None or raw.get("timeframe")==display_timeframe)', source)

    def test_scanner_chips_request_selected_timeframe(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('five_engine_chips(scan_symbol.value or "NIFTY",display_timeframe=scan_tf.value)', source)


class FiveEngineNonFiveMinuteSnapshotSafety(unittest.TestCase):
    def test_non_five_minute_chips_do_not_reuse_symbol_only_snapshot(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        start = source.index("    def five_engine_chips(sym, display_timeframe=None):")
        end = source.index("    def ", start + 5)
        function = source[start:end]
        self.assertIn('exact_frame=display_timeframe or "5m"', function)
        self.assertIn('read_five_engine_context(sym,exact_frame)', function)
        self.assertIn('exact_frame in ("1m","3m","5m")', function)
        self.assertNotIn('read_five_engine_context(sym,"5m")', function)
        self.assertIn('ContextualFiveEngineCache()', source)

class FiveEngineScannerDetailsTimeframeContract(unittest.TestCase):
    def test_scanner_details_use_scanner_timeframe(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('five_engine_summary(scan_symbol.value or "NIFTY",display_timeframe=scan_tf.value)', source)
        start = source.index("    def five_engine_summary(symbol, display_timeframe=None):")
        end = source.index("    def five_engine_chips(", start)
        summary = source[start:end]
        self.assertIn('exact_frame=display_timeframe or "5m"', summary)
        self.assertIn('read_five_engine_context(symbol,exact_frame)', summary)
        self.assertIn('not any(e.eligible and e.source=="Dhan"', summary)
        self.assertIn('candle_tf=(display_timeframe or ', summary)

class FiveEngineOptionContextTimeframeSafety(unittest.TestCase):
    def test_summary_option_source_uses_exact_selected_timeframe(self):
        """Never present cached 5m option readiness as 1m/3m diagnostics."""
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        functions=[n for n in ast.walk(tree)
                   if isinstance(n,ast.FunctionDef) and n.name=="five_engine_summary"]
        self.assertEqual(len(functions),1)
        option_calls=[n for n in ast.walk(functions[0])
                      if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                      and n.func.id=="option_component"]
        self.assertEqual(len(option_calls),2)
        for call in option_calls:
            self.assertEqual(len(call.args),2)
            self.assertIsInstance(call.args[1],ast.BoolOp)
            self.assertIsInstance(call.args[1].op,ast.Or)
            self.assertIsInstance(call.args[1].values[0],ast.Name)
            self.assertEqual(call.args[1].values[0].id,"display_timeframe")
            self.assertIsInstance(call.args[1].values[1],ast.Constant)
            self.assertEqual(call.args[1].values[1].value,"5m")

    def test_unverified_pcr_bad_values_never_become_readiness_chip(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        chips=[n for n in ast.walk(tree)
               if isinstance(n,ast.FunctionDef) and n.name=="five_engine_chips"]
        self.assertEqual(len(chips),1)
        chip_source=ast.get_source_segment(source,chips[0])
        self.assertIn('matching_option_context_for_symbol(sym)',chip_source)
        self.assertIn('historical_option_position(data,symbol=sym',chip_source)
        self.assertIn('position["available"]',chip_source)
        self.assertIn('!="LIVE_ONLY"',chip_source)
        self.assertIn(' • WAIT',chip_source)
        self.assertNotIn('data["pcr"]',chip_source)
        from v3_option_position import historical_option_position
        rows=[{"strike":i,"ce":{"oi":10},"pe":{"oi":20}} for i in range(100,107)]
        data={"source":"dhan","symbol":"TCS","expiry":"2099-12-31",
              "freshness":"unverified","signal_eligible":False,
              "atm_window":{"source":"dhan","freshness":"unverified",
                            "signal_eligible":False,"atm":103,"rows":rows}}
        for bad in (None,True,float("nan"),-1):
            result=historical_option_position(dict(data,pcr=bad),symbol="TCS",
                       expiry="2099-12-31",now=1795600000)
            self.assertFalse(result["live_vote_eligible"])
            self.assertNotIn("pcr",result)
        for freshness in ("live","verified",None):
            self.assertFalse(historical_option_position(dict(data,freshness=freshness),
                symbol="TCS",expiry="2099-12-31",now=1795600000)["available"])


class FiveEngineCrossScreenTimeframeContract(unittest.TestCase):
    def test_dashboard_superfive_and_analysis_explicit_timeframes(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        for expected in (
            'rows.append(five_engine_chips(sym,display_timeframe="1m"))',
            'five_engine_chips(index_name,display_timeframe="1m")',
            'five_engine_chips(row["symbol"],display_timeframe="5m")',
            'five_engine_summary(row["symbol"],display_timeframe="5m")',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, source)
        # Scanner analysis blocks are built once per analysis and never repaint;
        # a second box set there froze and contradicted the live Five Engine section.
        self.assertNotIn('five_engine_chips(sym,display_timeframe=tf)', source)
        self.assertNotIn('five_engine_chips(sym,display_timeframe=interval)', source)
        self.assertIn('note(basis),refresh_scan_boxes(),vote_display(', source)
        self.assertIn('scan_box_host=ft.Container()', source)

class FiveEnginePaperTradingTimeframeContract(unittest.TestCase):
    def test_paper_trading_has_explicit_timeframe(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('five_engine_chips(instrument,display_timeframe=("1m" if instrument in ("NIFTY","BANKNIFTY","SENSEX") else "5m"))', source)
        self.assertNotIn('context=[five_engine_chips(instrument),', source)

if __name__=="__main__":unittest.main()


class FiveEngineHistoricalTimeframePublishContract(unittest.TestCase):
    def test_completed_1m_3m_publish_paths_are_contextual_and_hist_only(self):
        from pathlib import Path
        app=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=app.index("    def publish_five_engine_historical(")
        end=app.index("    def read_five_engine_context(",start)
        helper=app[start:end]
        self.assertIn('timeframe not in ("1m","3m")',helper)
        self.assertIn('result.get("source")!="Dhan"',helper)
        self.assertIn('result.get("timeframe")!=timeframe',helper)
        self.assertIn('result.get("historical") is not True',helper)
        self.assertIn('result.get("live_verified") is not False',helper)
        self.assertIn('live_verified=False,freshness="historical_unverified"',helper)
        self.assertIn('generation=provider_generation[0]',helper)
        self.assertIn('snapshot=scanner_snapshot(historical_only)',helper)
        self.assertIn('publish_five_engine_historical(sym,"1m",result)',app)
        self.assertIn('publish_five_engine_historical(sym,interval,historical)',app)
        self.assertIn('if interval in ("1m","3m"):',app)

    def test_hist_only_snapshot_cannot_vote_live(self):
        from five_engine import ContextualFiveEngineCache, scanner_snapshot
        result={"source":"Dhan","historical":True,"live_verified":False,
                "freshness":"historical_unverified","timestamp":1234567890,
                "votes":[{"name":"EMA 9/21","vote":1},
                         {"name":"RSI 14","vote":1},
                         {"name":"MACD","vote":1}]}
        cache=ContextualFiveEngineCache()
        for tf in ("1m","3m"):
            with self.subTest(timeframe=tf):
                cache.publish(symbol="NIFTY",timeframe=tf,generation=4,
                              snapshot=scanner_snapshot(dict(result,timeframe=tf)))
                shown=cache.read(symbol="NIFTY",timeframe=tf,generation=4,
                                 now=1234567900,connected=True,market_open=True)
                self.assertEqual(shown["combined"]["coverage"],0)
                self.assertTrue(all(row.display()["state"]=="WAIT"
                                    for row in shown["engines"]))


class FiveEngineCompletedCandleDisplayContract(unittest.TestCase):
    def test_exact_frame_and_completed_candle_hist_only(self):
        from five_engine import completed_timeframe_candle_balance
        start=1800000000
        for tf,seconds in (("1m",60),("3m",180),("5m",300)):
            with self.subTest(timeframe=tf):
                bars=[[start+i*seconds,100,103,99,102,12] for i in range(8)]
                history={"source":"Dhan","_scanner_timeframe":tf,"bars":bars}
                now=start+8*seconds
                shown=completed_timeframe_candle_balance(history,tf,now=now)
                self.assertIsNotNone(shown)
                self.assertTrue(shown["historical"])
                self.assertFalse(shown["verified"])
                self.assertEqual((shown["bullish"],shown["bearish"]),(100,0))
                self.assertIsNone(completed_timeframe_candle_balance(
                    history,tf,now=start+7*seconds))
                self.assertIsNone(completed_timeframe_candle_balance(
                    dict(history,_scanner_timeframe="5m" if tf!="5m" else "1m"),
                    tf,now=now))
                self.assertIsNone(completed_timeframe_candle_balance(
                    dict(history,source="Yahoo Finance"),tf,now=now))
                self.assertIsNone(completed_timeframe_candle_balance(
                    dict(history,bars=bars[:6]),tf,now=now))
                # A forming ninth candle cannot distort the valid final eight.
                partial=bars+[[now,100,103,99,99,12]]
                self.assertEqual(completed_timeframe_candle_balance(
                    dict(history,bars=partial),tf,now=now),shown)
                broken=[list(x) for x in bars]
                broken[4][0]+=seconds/2
                self.assertIsNone(completed_timeframe_candle_balance(
                    dict(history,bars=broken),tf,now=now))
                malformed=[list(x) for x in bars]
                malformed[3][5]=-1
                self.assertIsNone(completed_timeframe_candle_balance(
                    dict(history,bars=malformed),tf,now=now))
                # Broken OHLC must not produce plausible historical percentages.
                for field,value in ((1,0),(2,99),(3,103),(4,float("nan"))):
                    invalid=[list(x) for x in bars]
                    invalid[5][field]=value
                    with self.subTest(timeframe=tf,field=field):
                        self.assertIsNone(completed_timeframe_candle_balance(
                            dict(history,bars=invalid),tf,now=now))
                # A future/gapped ninth candle must not be silently discarded.
                for timestamp in (now+seconds,now+3600,now-seconds/2):
                    broken_last=bars+[[timestamp,100,103,99,99,12]]
                    with self.subTest(timeframe=tf,final_timestamp=timestamp):
                        self.assertIsNone(completed_timeframe_candle_balance(
                            dict(history,bars=broken_last),tf,now=now))

    def test_all_three_five_box_display_paths_share_validated_hist_helper(self):
        import ast
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        selected=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)
                  and node.name in ("five_engine_summary","five_engine_chips")]
        self.assertEqual(len(selected),2)
        counts={}
        for node in selected:
            calls=[n for n in ast.walk(node) if isinstance(n,ast.Call)
                   and isinstance(n.func,ast.Name)
                   and n.func.id=="completed_timeframe_candle_balance"]
            counts[node.name]=len(calls)
        # Summary now validates both ONLINE and OFFLINE 1m/3m/5m C HIST.
        self.assertEqual(counts,{"five_engine_summary":4,"five_engine_chips":1})


class FiveEngineMainContextWiringContract(unittest.TestCase):
    def test_legacy_5m_publisher_mirrored_and_main_display_reads_context(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        self.assertIn('contextual_five_engine=ContextualFiveEngineCache()',source)
        self.assertIn('contextual_five_engine.publish(',source)
        self.assertIn('contextual_five_engine.read(',source)
        self.assertIn('symbol=sym,timeframe="5m",generation=provider_generation[0]',source)
        self.assertIn('read_five_engine_context(symbol,exact_frame)',source)
        self.assertIn('read_five_engine_context(sym,exact_frame)',source)
        self.assertIn('exact_frame=display_timeframe or "5m"',source)
        self.assertIn('contextual_five_engine.clear()',source)
        # Both failure publishers remain technical-only; both successful
        # publishers join independent C evidence with their actual 5m input.
        self.assertEqual(source.count('publish_five_engine_5m(sym,scanner_snapshot('),2)
        self.assertEqual(source.count('publish_five_engine_5m(sym,scanner_snapshot(watch_signal_cache[sym]))'),2)
        self.assertEqual(source.count('publish_five_engine_5m(sym,engine_snapshot)'),2)
        self.assertIn('engine_snapshot=await local_analysis_pool.run(scanner_snapshot_with_candle,',source)
        self.assertIn('publish_five_engine_5m(sym,engine_snapshot)',source)
        self.assertIn('deepcopy(result),snapshot,symbol=sym,timeframe="5m",now=time.time())',source)
        self.assertIn('deepcopy(engine_input),deepcopy(data),symbol=sym,timeframe="5m",',source)
        self.assertIn('now=time.time(),timing=engine_timing)',source)
        self.assertIn('five_engine_timing.update(engine_timing,symbol=sym,timeframe="5m",generation=generation)',source)
        self.assertNotIn('five_engine_snapshots[sym]=scanner_snapshot(',source)


class ContextualFiveEngineCacheContract(unittest.TestCase):
    def _verified_snapshot(self, timestamp=1234567890):
        from five_engine import EngineEvidence, compose_snapshot
        return compose_snapshot(technical=EngineEvidence(
            "technical", 75, 25, verified=True, timestamp=timestamp,
            source="Dhan", reason="independently verified fixture"))

    def test_symbol_timeframe_and_generation_are_isolated(self):
        from five_engine import ContextualFiveEngineCache
        cache=ContextualFiveEngineCache()
        cache.publish(symbol="NIFTY",timeframe="5m",generation=7,
                      snapshot=self._verified_snapshot())
        accepted=cache.read(symbol="NIFTY",timeframe="5m",generation=7,
                            now=1234567900,connected=True,market_open=True)
        self.assertEqual(accepted["combined"]["coverage"],1)
        for symbol,tf,gen in (("BANKNIFTY","5m",7),
                              ("NIFTY","1m",7),("NIFTY","3m",7),
                              ("NIFTY","5m",8)):
            with self.subTest(symbol=symbol,timeframe=tf,generation=gen):
                shown=cache.read(symbol=symbol,timeframe=tf,generation=gen,
                                 now=1234567900,connected=True,market_open=True)
                self.assertEqual(shown["combined"]["coverage"],0)
        self.assertEqual(len(cache),1)

    def test_closed_disconnected_stale_and_cleared_fail_closed(self):
        from five_engine import ContextualFiveEngineCache
        cache=ContextualFiveEngineCache()
        cache.publish(symbol="RELIANCE",timeframe="3m",generation=1,
                      snapshot=self._verified_snapshot())
        args=dict(symbol="RELIANCE",timeframe="3m",generation=1,now=1234567900)
        self.assertEqual(cache.read(**args,connected=True,market_open=True)
                         ["combined"]["coverage"],1)
        self.assertEqual(cache.read(**args,connected=False,market_open=True)
                         ["combined"]["coverage"],0)
        self.assertEqual(cache.read(**args,connected=True,market_open=False)
                         ["combined"]["coverage"],0)
        self.assertEqual(cache.read(**dict(args,now=1234569000),
                                    connected=True,market_open=True)
                         ["combined"]["coverage"],0)
        cache.clear()
        self.assertEqual(cache.read(**args,connected=True,market_open=True)
                         ["combined"]["coverage"],0)

    def test_malformed_publish_and_context_rejected(self):
        from five_engine import ContextualFiveEngineCache
        cache=ContextualFiveEngineCache()
        with self.assertRaises(ValueError):
            cache.publish(symbol="NIFTY",timeframe="1m",generation=0,snapshot={})
        with self.assertRaises(ValueError):
            cache.publish(symbol="NIFTY",timeframe="1m",generation=True,
                          snapshot=self._verified_snapshot())
        with self.assertRaises(ValueError):
            cache.read(symbol="NIFTY",timeframe="1d",generation=0,
                       now=1234567900,connected=True,market_open=True)


class R2CombinedIdentityContract(unittest.TestCase):
    def test_wrong_symbol_or_frame_cannot_publish_technical_or_candle_vote(self):
        from five_engine import scanner_snapshot_with_candle
        scan={"symbol":"NIFTY","timeframe":"1m","source":"Dhan",
              "timestamp":1800000000,"historical":False,"live_verified":True,
              "freshness":"verified_live",
              "votes":[{"name":"EMA 9/21","vote":1},
                       {"name":"RSI 14","vote":1},
                       {"name":"MACD","vote":1}]}
        self.assertTrue(scanner_snapshot(scan)["engines"][0].eligible)
        for symbol,frame in (("BANKNIFTY","1m"),("NIFTY","3m"),
                             ("NIFTY","2m"),("","1m")):
            with self.subTest(symbol=symbol,frame=frame):
                output=scanner_snapshot_with_candle(
                    scan,None,symbol=symbol,timeframe=frame,now=1800000060)
                self.assertFalse(output["engines"][0].eligible)
                self.assertFalse(output["engines"][1].eligible)
                self.assertEqual(output["combined"]["coverage"],0)
        matched=scanner_snapshot_with_candle(
            scan,None,symbol="NIFTY",timeframe="1m",now=1800000060)
        self.assertTrue(matched["engines"][0].eligible)
        self.assertEqual(matched["combined"]["coverage"],1)
        self.assertEqual(matched["combined"]["state"],"WAIT")


class R2PublisherOwnershipTests(unittest.TestCase):
    def test_mutable_caller_snapshot_cannot_change_cached_engine_evidence(self):
        from five_engine import ContextualFiveEngineCache
        cache=ContextualFiveEngineCache()
        rows=list(compose_snapshot(technical=EngineEvidence(
            "technical",80,20,verified=True,timestamp=1234567890,
            source="Dhan"))["engines"])
        snapshot={"engines":rows,"combined":{"state":"BEARISH","coverage":5}}
        args=dict(symbol="NIFTY",timeframe="5m",generation=1)
        cache.publish(**args,snapshot=snapshot)
        rows[0]=EngineEvidence("technical")
        snapshot["engines"]=[]
        snapshot["combined"]["coverage"]=0
        cached=cache.peek(**args)
        self.assertEqual(cached["combined"]["coverage"],1)
        self.assertEqual(cached["combined"]["state"],"WAIT")
        self.assertTrue(cached["engines"][0].eligible)
        self.assertEqual(cache.read(**args,now=1234567900,connected=True,
                                    market_open=True)["combined"]["coverage"],1)


class R2CandleTimestampSafetyTests(unittest.TestCase):
    def test_out_of_range_session_timestamp_abstains_in_hist_and_live(self):
        from five_engine import completed_timeframe_candle_balance, verified_candle_evidence
        for tf,seconds in (("1m",60),("3m",180),("5m",300)):
            with self.subTest(frame=tf):
                bars=[[1800000000+i*seconds,100,103,99,102,12] for i in range(31)]
                bars[-1][0]=1e30
                history=dict(source="Dhan",symbol="NIFTY",_scanner_timeframe=tf,
                             historical=False,live_verified=True,
                             freshness="verified_live",bars=bars)
                self.assertIsNone(completed_timeframe_candle_balance(history,tf,now=1800010000))
                self.assertFalse(verified_candle_evidence(
                    history,tf,now=1800010000,symbol="NIFTY").eligible)


class R2DirectionalSourceBoundaryTests(unittest.TestCase):
    def test_explicit_historical_or_unverified_flow_never_votes_live(self):
        from five_engine import futures_from_component, option_from_component
        sample=dict(source="Dhan",verified=True,contract="NIFTY-CONTRACT",
                    direction_basis="validated_trade_flow",bullish=75,bearish=25,
                    timestamp=1795000000,available=True,bias="BULLISH")
        for adapter in (futures_from_component,option_from_component):
            self.assertTrue(adapter(sample).eligible)
            for flags in (dict(historical=True),dict(live_verified=False),
                          dict(historical=True,live_verified=True)):
                with self.subTest(adapter=adapter.__name__,flags=flags):
                    self.assertFalse(adapter(dict(sample,**flags)).eligible)


class RFinalSelectedFrameTests(unittest.TestCase):
    def test_selected_frame_requires_independent_candle_revision_and_identity(self):
        from unittest.mock import patch
        from five_engine import selected_verified_frame_snapshot
        for frame,seconds in (("1m",60),("3m",180)):
            stamp=1800000000
            scan=dict(timestamp=stamp,timeframe=frame,votes=[
                {"name":"EMA 9/21","vote":1},{"name":"RSI 14","vote":1},
                {"name":"MACD","vote":1}])
            hist=dict(symbol="NIFTY",_scanner_timeframe=frame,source="Dhan",
                      historical=False,live_verified=True,freshness="exchange_verified")
            candle=EngineEvidence("candle",80,20,verified=True,
                                  timestamp=stamp+seconds,source="Dhan")
            args=dict(symbol="NIFTY",timeframe=frame,now=stamp+seconds)
            with patch("five_engine.verified_candle_evidence",return_value=candle):
                result=selected_verified_frame_snapshot(scan,hist,**args)
                self.assertEqual(result["combined"]["coverage"],2)
                self.assertEqual(result["combined"]["state"],"WAIT")
                for changed in (dict(cached=True),dict(symbol="SENSEX"),
                                dict(historical=True),dict(live_verified=False)):
                    self.assertIsNone(selected_verified_frame_snapshot(scan,dict(hist,**changed),**args))
                self.assertIsNone(selected_verified_frame_snapshot(dict(scan,timestamp=stamp-1),hist,**args))
                self.assertIsNone(selected_verified_frame_snapshot(dict(scan,symbol="SENSEX"),hist,**args))
    def test_selected_frame_publisher_is_wired(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        self.assertIn("frame_snapshot=selected_verified_frame_snapshot(",source)
        self.assertIn("generation=current_provider_generation,snapshot=frame_snapshot",source)
