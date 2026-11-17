#!/usr/bin/env python3
"""Stage one combined Oracle assessment repair bundle; NEVER changes production."""
import ast
import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROD=Path("/opt/bot-king-server")
STAGED={
    "assessment_state.py":("/tmp/botking_assessment_state_candidate_5gmfsvgf.py", None),
    "assessment_api.py":("/tmp/bk_assessment_reader_candidate_euhpna7v.py", "f436f396bcbbd19a5724401aa82aa4d8d3ad00a7857df5b49e8201495e8003ea"),
    "server.py":("/tmp/bk_candle_1m3m5m_candidate_w01lw23o.py", "a4191c5f0efb4e35b0682a219ca378082b20c027f5fa0c66201c44fbc580660e"),
}
ORIGINAL={
    "assessment_state.py":"b066d6d41cb0892f653e3fa18a49d3050627df34b9b8d732624f03aa40dfc8d4",
    "assessment_api.py":"91c0fc7e3ef95a6bfb63b54ded0f56f1d429f465a11830442419472e87dee57b",
    "server.py":"ef1f5cd971fd8129a1a704457b69014a37c7dc300178158f6b48dd91fd8d93a9",
}
def data(path,sha=None):
    p=Path(path)
    if not p.is_file() or p.is_symlink():raise RuntimeError("HOLD: missing or unsafe "+str(p))
    x=p.read_bytes()
    if sha and hashlib.sha256(x).hexdigest()!=sha:raise RuntimeError("HOLD: source SHA changed "+str(p))
    ast.parse(x.decode())
    return x.decode()
def get_function(tree,name):
    matches=[x for x in ast.walk(tree) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name]
    if len(matches)!=1:raise RuntimeError("HOLD: ambiguous function "+name)
    return matches[0]
def find_calls(fn,name):
    return [n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]

for name,sha in ORIGINAL.items():data(PROD/name,sha)
content={name:data(path,sha) for name,(path,sha) in STAGED.items()}
# Source-only last-bar validation: validates the 2 candidate rows and confirms last close time.
# Only the assessment publisher is guarded; historical chart cache is not mutated.
server=content["server.py"]
old='if interval in ("1", "3", "5") and len(entry.get("bars") or []) >= 2:'
new='''if (
                interval in ("1", "3", "5")
                and len(entry.get("bars") or []) >= 2
                and _assessment_bars_completed(entry["bars"][-2:], int(interval))
            ):'''
if server.count(old)!=1:raise RuntimeError("HOLD: candle publish guard anchor changed")
server=server.replace(old,new,1)
# Preserve FastAPI route registration: insert BEFORE its decorator, not after.
marker='    def cached_candles('
if server.count(marker)!=1:raise RuntimeError("HOLD: cached_candles anchor mismatch")
cached_fn=get_function(ast.parse(server),"cached_candles")
if len(cached_fn.decorator_list)!=1:
    raise RuntimeError("HOLD: wrong candle decorator count")
route_dec=cached_fn.decorator_list[0]
if not (isinstance(route_dec,ast.Call) and isinstance(route_dec.func,ast.Attribute)
        and isinstance(route_dec.func.value,ast.Name) and route_dec.func.value.id=="app"
        and route_dec.func.attr=="get"):
    raise RuntimeError("HOLD: missing existing FastAPI GET decorator")
route_lineno=route_dec.lineno
server_lines=server.splitlines(keepends=True)
if not server_lines[route_lineno-1].strip().startswith("@app.get("):
    raise RuntimeError("HOLD: unexpected route decorator anchor")
helper='''    def _assessment_bars_completed(rows, minutes):
        # Assessment quality gate only. Never affects the last-good chart cache.
        if minutes not in (1, 3, 5) or len(rows) != 2:
            return False
        previous = 0
        now = datetime.now(timezone.utc).timestamp()
        for bar in rows:
            if not isinstance(bar, (list, tuple)) or len(bar) != 6:
                return False
            if type(bar[0]) is not int or bar[0] <= previous:
                return False
            ts, op, hi, lo, cl, vol = bar
            if any(type(v) not in (int, float) for v in bar[1:]):
                return False
            if not all(math.isfinite(v) for v in (op, hi, lo, cl, vol)):
                return False
            if min(op, hi, lo, cl) <= 0 or vol < 0:
                return False
            if hi < max(op, lo, cl) or lo > min(op, hi, cl):
                return False
            previous = ts
        return rows[-1][0] + minutes * 60 <= now

'''
if "import math" not in server:raise RuntimeError("HOLD: math import missing")
if "from datetime import" not in server:raise RuntimeError("HOLD: datetime imports missing")
server="".join(server_lines[:route_lineno-1])+helper+"".join(server_lines[route_lineno-1:])
content["server.py"]=server
# Old clients with no explicit selector must not get potentially wrong evidence.
# Keep legacy cache read behavior intact for unrelated callers; filter at endpoint only.
api=content["assessment_api.py"]
tree=ast.parse(api)
fn=get_function(tree,"assessment")
calls=find_calls(fn,"read")
if len(calls)!=1:raise RuntimeError("HOLD: reader call count")
call=calls[0]
assignments=[n for n in ast.walk(fn) if isinstance(n,ast.Assign) and n.lineno==call.lineno and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="cached"]
if len(assignments)!=1 or call.lineno!=call.end_lineno:raise RuntimeError("HOLD: expected single-line cached assignment")
lines=api.splitlines(keepends=True)
indent=lines[call.lineno-1][:len(lines[call.lineno-1])-len(lines[call.lineno-1].lstrip())]
addition=(indent+'if timeframe is None:\n'+indent+'    cached.pop("candle", None)\n'+indent+'if expiry is None:\n'+indent+'    cached.pop("options", None)\n')
lines.insert(call.lineno,addition)
api="".join(lines)
content["assessment_api.py"]=api

# Validate all three syntactic contracts at once, no imports from Oracle project.
tr={k:ast.parse(v) for k,v in content.items()}
state_pub=get_function(tr["assessment_state.py"],"publish")
state_read=get_function(tr["assessment_state.py"],"read")
for f in (state_pub,state_read):
    if not {"timeframe","expiry"}<={a.arg for a in f.args.kwonlyargs}:raise RuntimeError("HOLD: selector state interface")
reader=get_function(tr["assessment_api.py"],"assessment")
if not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=="pop" for x in ast.walk(reader)):
    raise RuntimeError("HOLD: legacy evidence cleanup missing")
cand=get_function(tr["server.py"],"cached_candles")
if len(find_calls(cand,"publish"))!=1 or len(find_calls(get_function(tr["server.py"],"dhan_option_chain"),"publish"))!=1:
    raise RuntimeError("HOLD: publisher interface changed")
helper_ast=get_function(tr["server.py"],"_assessment_bars_completed")
route_ast=get_function(tr["server.py"],"cached_candles")
if helper_ast.decorator_list or len(route_ast.decorator_list)!=1:
    raise RuntimeError("HOLD: route decorator shifted to helper")
route_check=route_ast.decorator_list[0]
if not (isinstance(route_check,ast.Call) and isinstance(route_check.func,ast.Attribute)
        and isinstance(route_check.func.value,ast.Name) and route_check.func.value.id=="app"
        and route_check.func.attr=="get"):
    raise RuntimeError("HOLD: original candle route decorator missing")

bundle=Path(tempfile.mkdtemp(prefix="bk_oracle_joint_repair_",dir="/tmp"))
bundle.chmod(0o700)
manifest={}
for name,text in content.items():
    dest=bundle/name
    dest.write_text(text,encoding="utf-8")
    dest.chmod(0o600)
    manifest[name]={"sha256":hashlib.sha256(text.encode()).hexdigest(),"path":str(dest)}
print(json.dumps({
  "result":"ORACLE_JOINT_REPAIR_BUNDLE_STAGED",
  "bundle":str(bundle),
  "files":manifest,
  "fixes":["assessment_state_scope_timeframe_expiry","assessment_reader_selectors","legacy_no_selector_fail_closed","1m_3m_5m_candle_publish","options_expiry_publish","assessment_candle_last_bar_closed_guard"],
  "scope":"SOURCE_AND_AST_ONLY",
  "runtime_http_tested":False,"dhan_data_tested":False,"production_changed":False,
  "server_restarted":False,"dhan_requests":0,"orders_sent":0,"release_approved":False
},indent=2))
