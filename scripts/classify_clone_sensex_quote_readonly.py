#!/usr/bin/env python3
"""Read-only, offline SENSEX quote response classification.

Input must be a SANITIZED JSON file holding only either:
  {"quotes":{"NIFTY":{"ltp":1},"BANKNIFTY":{"ltp":1}},"unavailable":["SENSEX"]}
or:
  {"status":"success","data":{"IDX_I":{"13":{"last_price":1},"25":{"last_price":1}},"BSE_I":{}}}
Never feed raw broker logs, authorization headers, tokens, SSK or full snapshots.
No requests, imports of runtime modules, environment access or secret output.
"""
import argparse
import json
import math
from pathlib import Path

MAPPING = {"NIFTY": ("IDX_I", "13"), "BANKNIFTY": ("IDX_I", "25"), "SENSEX": ("BSE_I", "51")}


def valid(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def classify(data):
    if not isinstance(data, dict):
        return {"kind": "INVALID_SHAPE", "indices": {}}
    result = {}
    if isinstance(data.get("quotes"), dict) and isinstance(data.get("unavailable"), list):
        for name in MAPPING:
            row = data["quotes"].get(name)
            if isinstance(row, dict) and valid(row.get("ltp")):
                result[name] = "VALID_UNVERIFIED"
            elif name in data["unavailable"]:
                result[name] = "PROVIDER_UNAVAILABLE_OR_REJECTED"
            else:
                result[name] = "MISSING_OR_INVALID_GATEWAY_FIELD"
        return {"kind": "CLONE_GATEWAY_PARTIAL_QUOTE", "indices": result,
                "provider_root_cause_proven": False}
    if isinstance(data.get("data"), dict):
        for name, (segment, sid) in MAPPING.items():
            seg = data["data"].get(segment)
            item = seg.get(sid) if isinstance(seg, dict) else None
            if not isinstance(seg, dict):
                result[name] = "SEGMENT_MISSING"
            elif not isinstance(item, dict):
                result[name] = "SECURITY_ID_MISSING"
            elif valid(item.get("last_price")):
                result[name] = "VALID_UNVERIFIED"
            else:
                result[name] = "INVALID_LAST_PRICE"
        return {"kind": "SANITIZED_PROVIDER_BATCH", "indices": result,
                "provider_root_cause_proven": False}
    return {"kind": "UNRECOGNIZED_SANITIZED_FORMAT", "indices": {}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("sanitized_json", type=Path)
    args = p.parse_args()
    path = args.sanitized_json
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 10000:
        raise SystemExit("Expected a small regular sanitized JSON file")
    body = json.loads(path.read_text(encoding="utf-8"))
    # Only controlled classification labels are printed: never echo file contents.
    print(json.dumps(classify(body), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
