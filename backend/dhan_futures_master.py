"""Parse official Dhan DETAILED instrument CSV into unverified FUT candidates.

The Dhan DETAILED CSV has EXCH_ID, SEGMENT, INSTRUMENT and UNDERLYING_SYMBOL.
The COMPACT SEM_* CSV does not expose UNDERLYING_SYMBOL, so it is rejected.
Parsing alone cannot verify origin, freshness, entitlement or live trade flow.
Never promote parsed candidates to authenticated futures mappings.
"""
import csv
import io
from datetime import date, datetime

REQUIRED=frozenset(("EXCH_ID","SEGMENT","INSTRUMENT","UNDERLYING_SYMBOL",
                    "SECURITY_ID","SM_EXPIRY_DATE","DISPLAY_NAME"))


def futures_candidates_from_dhan_detailed(csv_text, *, max_bytes=8000000):
    if not isinstance(csv_text,str) or len(csv_text.encode("utf-8"))>max_bytes:
        raise ValueError("Bounded detailed Dhan CSV text required")
    reader=csv.DictReader(io.StringIO(csv_text,newline=""))
    if not reader.fieldnames or not REQUIRED.issubset(set(reader.fieldnames)):
        raise ValueError("Dhan detailed master required columns missing")
    result=[]
    seen=set()
    security_id_owner={}
    contract_owner={}
    for index,row in enumerate(reader):
        if index>=500000:
            raise ValueError("Master exceeds safe row count")
        if not isinstance(row,dict) or None in row:
            raise ValueError("Malformed Dhan detailed master row")
        if row.get("EXCH_ID")!="NSE" or row.get("SEGMENT")!="D":
            continue
        if row.get("INSTRUMENT") not in ("FUTIDX","FUTSTK"):
            continue
        symbol=(row.get("UNDERLYING_SYMBOL") or "").strip()
        sid=(row.get("SECURITY_ID") or "").strip()
        contract=(row.get("DISPLAY_NAME") or "").strip()
        raw_expiry=(row.get("SM_EXPIRY_DATE") or "").strip()
        if (not symbol or len(symbol)>32 or
                not all(c.isupper() or c.isdigit() or c in "&_-" for c in symbol)
                or not sid.isascii() or not sid.isdecimal() or int(sid)<=0
                or not contract or len(contract)>128):
            raise ValueError("Unsafe Futures master identity")
        try:
            expiry=date.fromisoformat(raw_expiry)
        except ValueError:
            raise ValueError("Futures expiry format invalid") from None
        if raw_expiry!=expiry.isoformat():
            raise ValueError("Futures expiry not ISO")
        identity=(symbol,expiry.isoformat(),sid)
        if identity in seen:
            raise ValueError("Duplicate Futures instrument master identity")
        seen.add(identity)
        # Every NSE_FNO security ID must identify only ONE contract in the
        # current snapshot; otherwise the source master is inconsistent.
        if sid in security_id_owner:
            raise ValueError("Conflicting Futures security ID across contracts")
        security_id_owner[sid]=(symbol,expiry.isoformat(),contract)
        contract_identity=(symbol,expiry.isoformat(),contract)
        if contract_identity in contract_owner:
            raise ValueError("Duplicate Futures contract with distinct security IDs")
        contract_owner[contract_identity]=sid
        result.append({"source":"Dhan","master_verified":False,
                       "instrument_type":"FUT","exchange_segment":"NSE_FNO",
                       "underlying":symbol,"expiry":expiry.isoformat(),
                       "security_id":sid,"contract":contract,
                       "provenance":"UNVERIFIED_DETAILED_CSV_PARSE_ONLY"})
        if len(result)>150000:
            raise ValueError("Futures candidate count too large")
    return result


def futures_master_readiness(rows):
    """Static diagnostics. Never set master_verified or signal_eligible."""
    return {"mode":"FUTURES_DETAILED_MASTER_PARSE_ONLY",
            "candidate_count":len(rows),
            "provider_requests":0,"orders_sent":0,
            "authenticated_master":False,
            "mapping_eligible":False,
            "next_step":"VERIFY_OFFICIAL_DHAN_DOWNLOAD_PROVENANCE_FRESHNESS_AND_MASTER_BEFORE_OPERATOR_APPROVAL"}
