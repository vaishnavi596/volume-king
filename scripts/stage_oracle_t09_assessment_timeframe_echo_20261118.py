#!/usr/bin/env python3
"""SHA-locked offline T09 Assessment timeframe echo patch. Stage only, never deploy.
No import of Oracle server modules, no network/Dhan/order, no prod writes.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile

SOURCE = Path("/opt/bot-king-server/assessment_api.py")
EXPECTED = "f421292725adadd825cbfa2a2a14f358aa6d07f29e3d71c0aa073d4b2827a2a5"

def stage_source(raw):
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("ASSESSMENT_API_SHA_DRIFT")
    tree = ast.parse(raw.decode("utf-8"))
    fs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name=="assessment"]
    if len(fs)!=1: raise ValueError("ASSESSMENT_FUNCTION_NOT_UNIQUE")
    fn=fs[0]
    if len(fn.body)<2 or not isinstance(fn.body[-1],ast.Return) or not isinstance(fn.body[-1].value,ast.Name) or fn.body[-1].value.id!="data":
        raise ValueError("RETURN_DATA_ANCHOR_CHANGED")
    if fn.body[-1].lineno != 84 or fn.lineno != 26:
        raise ValueError("ASSESSMENT_LINEAGE_CHANGED")
    args={x.arg for x in fn.args.args+fn.args.kwonlyargs}
    if not {"symbol","timeframe","expiry","x_botking_key"} <= args:
        raise ValueError("SELECTOR_ARGS_CHANGED")
    if any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=="data" and isinstance(n.slice,ast.Constant) and n.slice.value=="timeframe" for n in ast.walk(fn)):
        raise ValueError("TIMEFRAME_ALREADY_ASSIGNED")
    if len([n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="read"])!=1:
        raise ValueError("CACHE_READER_CALL_CHANGED")
    if any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="data" for t in n.targets) for n in ast.walk(fn)) is False:
        raise ValueError("DATA_ASSIGNMENT_MISSING")
    lines=raw.decode("utf-8").splitlines(keepends=True)
    ret=fn.body[-1]
    original_line=lines[ret.lineno-1]
    indent=original_line[:len(original_line)-len(original_line.lstrip())]
    if original_line.strip()!="return data":
        raise ValueError("RETURN_LINE_MISMATCH")
    # Echo only the already validated selector; never alter evidence or signal eligibility.
    extra=indent+"if not isinstance(data, dict):\n"+indent+"    raise TypeError('ASSESSMENT_RESPONSE_SHAPE')\n"+indent+"data = dict(data)\n"+indent+"data['timeframe'] = timeframe\n"
    lines.insert(ret.lineno-1,extra)
    patched="".join(lines).encode()
    new=ast.parse(patched.decode())
    news=[n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name=="assessment"]
    if len(news)!=1 or not isinstance(news[0].body[-1],ast.Return):
        raise ValueError("PATCH_STRUCTURE_CHANGED")
    # AST outside the target handler must remain identical.
    import copy
    restore=copy.deepcopy(new)
    funcs=[n for n in ast.walk(restore) if isinstance(n,ast.FunctionDef) and n.name=="assessment"]
    funcs[0].body=copy.deepcopy(fn.body)
    if ast.dump(restore)!=ast.dump(tree):
        raise ValueError("OUTSIDE_HANDLER_CHANGED")
    return patched

def main():
    report={"audit":"T09_ASSESSMENT_ECHO_STAGE","production_changed":False,
            "server_restarted":False,"dhan_requests":0,"orders_sent":0}
    try:
        raw=SOURCE.read_bytes()
        patched=stage_source(raw)
        dest=Path(tempfile.mkdtemp(prefix="botking-t09-echo-",dir="/tmp"))/"assessment_api.py"
        dest.write_bytes(patched)
        dest.chmod(0o600)
        report.update(status="STAGED_ONLY",source_sha256=hashlib.sha256(raw).hexdigest(),
                      candidate_sha256=hashlib.sha256(patched).hexdigest(),
                      candidate_path=str(dest),runtime_verified=False,deploy_approved=False)
    except Exception as exc:
        report.update(status="HOLD",error_type=type(exc).__name__)
    print(json.dumps(report,indent=2))
    return 0 if report["status"]=="STAGED_ONLY" else 2

if __name__=="__main__":
    sys.exit(main())
