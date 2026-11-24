"""Strict, no-network Futures contract + Dhan LTP context adapter.

Provisioning needs a separately authenticated Dhan instrument master. The
operator-supplied master is a trusted server-side dependency, not phone input.
An LTP cannot establish directional trade flow or exchange-time freshness.
"""
from datetime import date, datetime
from math import isfinite


def select_verified_future(rows, symbol, expiry):
    if (not isinstance(symbol,str) or not symbol.strip()
            or not isinstance(expiry,date) or isinstance(expiry,datetime)
            or not isinstance(rows,(list,tuple))):
        return None
    matching=[]
    for row in rows:
        if not isinstance(row,dict):
            continue
        if (row.get("source")!="Dhan" or row.get("master_verified") is not True
                or row.get("instrument_type")!="FUT"
                or row.get("exchange_segment")!="NSE_FNO"
                or row.get("underlying")!=symbol
                or row.get("expiry")!=expiry.isoformat()):
            continue
        sid=row.get("security_id")
        contract=row.get("contract")
        if (not isinstance(sid,str) or not sid.isascii() or not sid.isdecimal()
                or int(sid)<=0 or not isinstance(contract,str)
                or not contract.strip()):
            return None
        matching.append({"symbol":symbol,"underlying":symbol,
                         "expiry":expiry.isoformat(),"contract":contract.strip(),
                         "security_id":sid})
        if len(matching)>1:
            return None
    return matching[0] if len(matching)==1 else None


def normalize_futures_ltp(raw,mapping):
    """Return only source LTP context; no invented OI, volume, direction."""
    if not isinstance(raw,dict) or raw.get("status")!="success":
        return None
    data=raw.get("data")
    values=data.get("NSE_FNO") if isinstance(data,dict) else None
    row=values.get(mapping["security_id"]) if isinstance(values,dict) else None
    price=row.get("last_price") if isinstance(row,dict) else None
    if type(price) not in (int,float) or not isfinite(price) or price<=0:
        return None
    return {"source":"dhan","symbol":mapping["symbol"],
            "underlying":mapping["underlying"],"expiry":mapping["expiry"],
            "contract":mapping["contract"],"exchange_segment":"NSE_FNO",
            "ltp":float(price),"mapping_verified":True,
            "freshness":"unverified","direction_verified":False,
            "signal_eligible":False,"direction":None,
            "live_orders_enabled":False}
