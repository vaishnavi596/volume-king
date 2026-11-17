#!/usr/bin/env python3
"""One grouped offline regression of staged Oracle joint repair; no app/server imports."""
import ast
import hashlib
import importlib.util
import json
import math
import time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path("/tmp/bk_oracle_joint_repair_jtzebav3")
EXPECTED={
"assessment_state.py":"ea2db1787be5cddc1ff2235db6592c7858519fc97b18d8c65c011ef9c7a3e3d2",
"assessment_api.py":"f421292725adadd825cbfa2a2a14f358aa6d07f29e3d71c0aa073d4b2827a2a5",
"server.py":"b6ba77057a92fa8b33da64af1c242a0c802e0bd78ce4370dfe118ce51b45ac61",
}
checks={}
def record(k,v):
    checks[k]="PASS" if v else "FAIL"
def function(tree,name):
    f=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(f)!=1:raise AssertionError("missing/ambiguous function "+name)
    return f[0]
def calls(f,name):
    return [n for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]

trees={}
for file,sha in EXPECTED.items():
    p=ROOT/file
    if not p.is_file() or p.is_symlink():raise RuntimeError("HOLD: missing staged file "+file)
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise RuntimeError("HOLD: bundle SHA drift "+file)
    trees[file]=ast.parse(raw.decode())
record("three_file_exact_sha_syntax",True)

# Avoid importing the app or running its factory. Isolate only cache-state module.
state_fn=ROOT/"assessment_state.py"
spec=importlib.util.spec_from_file_location("bk_stage_joint_cache_test",state_fn)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.clear()
m.publish("acc_A","NIFTY","candle",{"bars":[[1,10,11,9,10.5,100],[181,11,12,10,11.5,100]]},timeframe="3m")
m.publish("acc_A","NIFTY","candle",{"bars":[[1,10,11,9,10.5,100],[61,11,12,10,11.5,100]]},timeframe="1m")
m.publish("acc_A","NIFTY","options",{"expiry":"2099-01-01","option_metrics":{"pcr":0.8}},expiry="2099-01-01")
m.publish("acc_A","NIFTY","options",{"expiry":"2099-01-08","option_metrics":{"pcr":1.4}},expiry="2099-01-08")
m.publish("acc_A","NIFTY","futures",{"direction":"bullish"})
a=m.read("acc_A","NIFTY",timeframe="1m",expiry="2099-01-08")
bb=m.read("acc_A","NIFTY",timeframe="3m",expiry="2099-01-01")
record("scope_timeframe_expiry_futures_one_read", a["candle"]["bars"][-1][0]==61 and bb["candle"]["bars"][-1][0]==181 and a["options"]["option_metrics"]["pcr"]==1.4 and bb["options"]["option_metrics"]["pcr"]==0.8 and "futures" in a)
record("missing_selector_evidence_not_reused","candle" not in m.read("acc_A","NIFTY",timeframe="5m") and "options" not in m.read("acc_A","NIFTY",expiry="2099-01-15"))
record("account_scope_isolated", not m.read("acc_B","NIFTY",timeframe="1m",expiry="2099-01-01"))
m.clear()

# Ensure FastAPI original route registration survives helper insertion.
helper=function(trees["server.py"],"_assessment_bars_completed")
candle_route=function(trees["server.py"],"cached_candles")
def is_get_route(dec):
    return (isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute)
            and isinstance(dec.func.value,ast.Name)
            and dec.func.value.id=="app" and dec.func.attr=="get")
record("candle_route_decorator_preserved",
       not helper.decorator_list and len(candle_route.decorator_list)==1
       and is_get_route(candle_route.decorator_list[0]))
if not checks["candle_route_decorator_preserved"]=="PASS":
    raise RuntimeError("HOLD: a helper stole the FastAPI route decorator")
namespace={"datetime":datetime,"timezone":timezone,"math":math}
exec(compile(ast.Module(body=[helper],type_ignores=[]),"<stage_helper>","exec"),namespace)
completed=namespace["_assessment_bars_completed"]
now=int(time.time())
def bar(ts,o=100,h=102,lo=99,c=101,vol=1000):
    return [ts,o,h,lo,c,vol]
for interval in (1,3,5):
    full=[bar(now-interval*60*4),bar(now-interval*60*2)]
    partial=[bar(now-interval*60*3),bar(now-interval*60+5)]
    record("last_candle_%dm_closed_only"%interval,completed(full,interval) and not completed(partial,interval))
record("ohlc_and_order_rejected",not completed([bar(now-600),bar(now-400,h=90)],1) and not completed([bar(now-400),bar(now-600)],1))
record("invalid_type_rejected",not completed([bar(now-500),bar(now-400,vol=True)],1))

# Reader: check auth remains in handler plus that evidence is removed after cache read
# whenever a corresponding request selector is missing.
reader=function(trees["assessment_api.py"],"assessment")
reads=calls(reader,"read")
assert len(reads)==1
record("reader_both_selectors_forwarded", {kw.arg for kw in reads[0].keywords}=={"timeframe","expiry"})
source=ast.unparse(reader)
record("legacy_unqualified_candle_suppressed", 'if timeframe is None:' in source and "cached.pop('candle', None)" in source)
record("legacy_unqualified_options_suppressed", 'if expiry is None:' in source and "cached.pop('options', None)" in source)
# Only static auth evidence: do not claim protected HTTP flow is runtime validated.
record("auth_reference_present", "x_botking_key" in source)
publisher=function(trees["server.py"],"cached_candles")
record("guard_wired_into_candle_publisher", len(calls(publisher,"_assessment_bars_completed"))==1 and len(calls(publisher,"publish"))==1)
opt=function(trees["server.py"],"dhan_option_chain")
record("options_publish_expiry", len(calls(opt,"publish"))==1 and "expiry" in {k.arg for k in calls(opt,"publish")[0].keywords})
summary={"PASS":sum(v=="PASS" for v in checks.values()),"FAIL":sum(v=="FAIL" for v in checks.values())}
print(json.dumps({"audit":"BOT_KING_FINAL_STAGED_JOINT_OFFLINE_REGRESSION","bundle":str(ROOT),"checks":checks,"summary":summary,"scope":"OFFLINE_SYNTHETIC_AND_AST","http_auth_runtime_verified":False,"actual_dhan_market_data_verified":False,"production_changed":False,"server_restarted":False,"orders_sent":0,"dhan_requests":0,"release_approved":False},indent=2,sort_keys=True))
if summary["FAIL"]:raise SystemExit(2)
