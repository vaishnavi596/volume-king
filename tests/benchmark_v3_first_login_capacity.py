"""BOT KING V3 offline 70-equity first-login benchmark. No Dhan/Oracle/Android calls.
Run: PYTHONPATH=src python tests/benchmark_v3_first_login_capacity.py
Measures real Python adapter/compute/queue operations on GitHub runner, NOT Flutter render.
"""
from __future__ import annotations
import copy
import json
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))
from analysis_quality import quality_check
from scanner_engine import analyze
from dhan_three_minute import completed_three_minute_bars
from clone_day2_apply_queue import SmartApplyQueue, Update

IST=timezone(timedelta(hours=5,minutes=30))
TF=("1m","3m","5m")
FIVE=("oi_support","oi_resistance","max_pain","pcr","candle_trend")
INDICATORS=("Supertrend","EMA 9/21","RSI 14","MACD","VWAP")
START=int(datetime(2026,11,20,9,15,tzinfo=IST).timestamp())
NOW=float(START+250*60)
FRAME_SECONDS=0.016
def millis(s):return round(s*1000,3)

def bars_for(n):
    base=1100+4*n
    return [[START+i*60,base+i*.06,base+i*.06+.8,base+i*.06-.8,
             base+i*.06+.12,10000+i*2] for i in range(180)]

def five_minute_bars(rows):
    out=[]
    for i in range(0,len(rows)-4,5):
        group=rows[i:i+5]
        out.append([group[0][0],group[0][1],max(b[2] for b in group),
                    min(b[3] for b in group),group[-1][4],sum(b[5] for b in group)])
    return out

def make_payload(equities):
    ids=[f"EQ{i:02}" for i in range(equities)]+["NIFTY","BANKNIFTY","SENSEX"]
    payload={}
    for i,sym in enumerate(ids):
        one=bars_for(i)
        three=completed_three_minute_bars(one,now_epoch=NOW)
        five=five_minute_bars(one)
        payload[sym]={"source":"Dhan","quote":{"price":one[-1][4],"freshness":"unverified"},
                      "candles":{"1m":one,"3m":three,"5m":five},
                      "options":{"pcr":1.1,"max_pain":int(one[-1][4]//10)*10},
                      "status":"historical_unverified"}
    return payload

def run_case(equities):
    start=time.perf_counter()
    inbound=make_payload(equities)
    payload_bytes=len(json.dumps(inbound,separators=(",",":")))
    t_payload=time.perf_counter()
    # Validated app-owned stock; same-source, keyed by generation/symbol/timeframe.
    stock={}
    for sym,row in inbound.items():
        assert row["source"]=="Dhan"
        assert row["quote"]["price"]>0
        for tf,bars in row["candles"].items():
            assert tf in TF and bars and all(b[3]<=min(b[1],b[4])<=max(b[1],b[4])<=b[2] for b in bars)
        stock[(1,sym)]=copy.deepcopy(row)
    t_stock=time.perf_counter()
    # Actual BOT KING scanner technical analysis on each timeframe. These 5 technical
    # indicators are NOT a proof of five option/OI filters (which need broker evidence).
    computed={}
    for (generation,sym),row in stock.items():
        details={}
        for tf,bars in row["candles"].items():
            seconds={"1m":60,"3m":180,"5m":300}[tf]
            qc=quality_check(bars,seconds,now=NOW)
            # Historical fixture, not exchange verified/live or option/OI scores.
            analysis=analyze(qc["bars"],list(INDICATORS),tf)
            details[tf]={"quality":qc["completed_count"],"votes":len(analysis.get("votes",[])),
                         "bias":analysis["bias"],"timestamp":analysis.get("timestamp")}
        # These five UI filter slots can only stay unavailable when no verified OI
        # evidence exists: no fabricated bullish/bearish signal is permitted.
        details["filters"]={k:{"status":"WAIT","eligible":False} for k in FIVE}
        computed[sym]=details
    t_compute=time.perf_counter()
    q=SmartApplyQueue(max_pending=512)
    expected=0
    for (_,sym),row in stock.items():
        for update in [Update("watchlist",sym,"quote",1,row["quote"]["price"])] + [
            Update("chart",sym,"candle",1,computed[sym][tf],tf,completed=True) for tf in TF
        ] + [
            Update("scanner",sym,k,1,computed[sym]["filters"][k]) for k in FIVE
        ] + [Update("dashboard",sym,"assessment",1,{"status":"WAIT"})]:
            expected+=1
            q.receive(update)
    t_queue=time.perf_counter()
    # Simulates Python-side Mounted-Control property assignment and JSON serialization;
    # does NOT call Flet page.update(), cross the WebSocket, or paint Flutter frames.
    controls={}
    while q.pending:
        def fake_control_update(u):
            controls[(u.section,u.symbol,u.kind,u.timeframe)]=json.dumps(u.value)
        report=q.apply_tick(16,fake_control_update)
        if report.errors:raise RuntimeError(report.errors)
    t_apply=time.perf_counter()
    return {"equities":equities,"indices":3,"instruments":len(inbound),
        "synthetic_bytes":payload_bytes,"expected_ui_updates":expected,
        "queue_admitted":q.counts["queued"],"queue_rejected":q.counts["capacity_rejected"],
        "python_applied":q.counts["applied"],
        "fixture_generate_ms":millis(t_payload-start),
        "validate_stock_ms":millis(t_stock-t_payload),
        "real_technical_compute_ms":millis(t_compute-t_stock),
        "queue_enqueue_ms":millis(t_queue-t_compute),
        "python_fake_control_apply_ms":millis(t_apply-t_queue),
        "measured_stock_to_python_apply_ms":millis(t_apply-t_payload),
        "android_flutter_render_ms":"NOT_MEASURED",
        "five_oi_filters_status":"WAIT_NO_VERIFIED_OI_EVIDENCE"}

def main():
    results=[run_case(n) for n in (7,32,51,70)]
    for item in results:
        print("V3_OFFLINE_BENCHMARK "+json.dumps(item,sort_keys=True))
    assert all(x["instruments"]==x["equities"]+3 for x in results)
    assert results[-1]["queue_rejected"]>0
    assert all(x["python_applied"]==min(x["expected_ui_updates"],512) for x in results)
    assert all(x["python_applied"]==x["queue_admitted"] for x in results)
    print("V3_OFFLINE_BENCHMARK_DONE: Python-only; Flet/Flutter device throughput UNVERIFIED")
if __name__=="__main__":main()
