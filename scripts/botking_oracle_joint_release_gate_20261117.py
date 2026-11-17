#!/usr/bin/env python3
"""One-shot, read-only Oracle five-filter integration gate. No app imports or Dhan calls."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path("/opt/bot-king-server")
TMP=Path("/tmp")
SOURCES={
"server.py":"ef1f5cd971fd8129a1a704457b69014a37c7dc300178158f6b48dd91fd8d93a9",
"assessment_api.py":"91c0fc7e3ef95a6bfb63b54ded0f56f1d429f465a11830442419472e87dee57b",
"assessment_state.py":"b066d6d41cb0892f653e3fa18a49d3050627df34b9b8d732624f03aa40dfc8d4",
"assessment_snapshot.py":"9330a1fa28d33526b3e6302c236149e2185a87a212a088e595cbd3b6c24ea455",
"backend/candle_resampler.py":"4c1758b1ffaa2feb193688913456aee337d861e5553d7469f116337fe17efed7",
}
STAGED={
"state":("botking_assessment_state_candidate_5gmfsvgf.py",None),
"reader":("bk_assessment_reader_candidate_euhpna7v.py","f436f396bcbbd19a5724401aa82aa4d8d3ad00a7857df5b49e8201495e8003ea"),
"publisher":("bk_candle_1m3m5m_candidate_w01lw23o.py","a4191c5f0efb4e35b0682a219ca378082b20c027f5fa0c66201c44fbc580660e"),
}
def load(p,sha):
    if not p.is_file() or p.is_symlink():return None,"MISSING_OR_UNSAFE"
    raw=p.read_bytes()
    if sha and hashlib.sha256(raw).hexdigest()!=sha:return None,"SHA_CHANGED"
    try:return ast.parse(raw.decode()),"PASS"
    except (SyntaxError,UnicodeError):return None,"SYNTAX_FAIL"
def fn(t,name):
    if t is None:return None
    a=[n for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    return a[0] if len(a)==1 else None
def call(f,name):
    if f is None:return []
    return [n for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]
def kw(f,name,keys):
    a=call(f,name)
    return len(a)==1 and keys<={k.arg for k in a[0].keywords}
trees,source_status={},{}
for name,sha in SOURCES.items():trees[name],source_status[name]=load(ROOT/name,sha)
stage,stage_status={},{}
for name,(file,sha) in STAGED.items():stage[name],stage_status[name]=load(TMP/file,sha)
gates={}
def gate(name,ok,reason):
    gates[name]={"status":"PASS" if ok else "OPEN","detail":"SOURCE_ONLY" if ok else reason}
gate("production_source_anchor",all(v=="PASS" for v in source_status.values()),"Source changed or missing: halt patches")
gate("staged_source_anchor",all(v=="PASS" for v in stage_status.values()),"Stage missing or modified")
sp=fn(stage["state"],"publish");sr=fn(stage["state"],"read")
gate("scoped_cache_contract",bool(sp and sr and {"timeframe","expiry"}<={a.arg for a in sp.args.kwonlyargs} and {"timeframe","expiry"}<={a.arg for a in sr.args.kwonlyargs}),"Selector-compatible state unavailable")
gate("reader_wiring",kw(fn(stage["reader"],"assessment"),"read",{"timeframe","expiry"}),"Reader selector wiring absent")
p=fn(stage["publisher"],"cached_candles")
pc=call(p,"publish")
gate("1m_3m_5m_candle_wiring",len(pc)==1 and {k.arg for k in pc[0].keywords}=={"timeframe"} and any(isinstance(n,ast.If) and {"1","3","5"}<={c.value for c in ast.walk(n.test) if isinstance(c,ast.Constant) and isinstance(c.value,str)} for n in ast.walk(p)) if p else False,"Candle publisher not qualified for all three timeframes")
gate("options_expiry_wiring",kw(fn(stage["publisher"],"dhan_option_chain"),"publish",{"expiry"}),"Expiry publisher missing")
gate("production_reader_wired",kw(fn(trees["assessment_api.py"],"assessment"),"read",{"timeframe","expiry"}),"Production reader still unqualified")
prod_state=fn(trees["assessment_state.py"],"publish")
gate("production_state_wired",bool(prod_state and {"timeframe","expiry"}<={a.arg for a in prod_state.args.kwonlyargs}),"Production cache still lacks selector key")
raw_pub=fn(trees["server.py"],"cached_candles")
gate("production_candle_selector",kw(raw_pub,"publish",{"timeframe"}),"Production publisher still 5m-only")
gate("3m_aggregate_present",fn(trees["backend/candle_resampler.py"],"aggregate") is not None,"Oracle resampler missing")
for name,reason in {
"direct_last_candle_completed":"No complete final-bar proof for direct 1m/5m before assessment publish",
"legacy_client_without_selectors":"Old GET without selectors needs explicit fail-closed policy",
"authenticated_http_integration":"FastAPI route/auth/expiry/timeframe runtime test not performed",
"source_freshness_and_five_filters":"Real evidence eligibility and five active filters not verified",
"mobile_trigger_and_release":"1m/3m mobile refresh and signed APK not verified",
}.items():gates[name]={"status":"BLOCKED","detail":reason}
counts={s:sum(x["status"]==s for x in gates.values()) for s in ("PASS","OPEN","BLOCKED")}
print(json.dumps({"audit":"BOT_KING_ONE_SHOT_ORACLE_INTEGRATION","source_status":source_status,"staged_status":stage_status,"gates":gates,"summary":counts,"source_only":True,"production_changed":False,"server_restarted":False,"dhan_requests":0,"orders_sent":0,"release_approved":False},indent=2,sort_keys=True))
