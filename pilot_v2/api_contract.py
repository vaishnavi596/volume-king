"""Versioned offline V2 gateway/mobile contract. No HTTP or trading."""
from math import isfinite
from .gateway_contract import ContractError, plan_demand, symbol_ok

API_PREFIX="/v2-pilot"
SCHEMA_VERSION=1
ENABLED_BY_DEFAULT=False

def parse_selection(body):
    if type(body) is not dict or set(body)!={"watchlists"}:
        raise ContractError("Invalid selection payload")
    groups=body["watchlists"]
    if type(groups) is not list or len(groups)!=5 or any(type(g) is not list for g in groups):
        raise ContractError("Exactly five watchlists required")
    demand=plan_demand(groups)
    return demand

def validate_snapshot(p):
    required={"protocol","schema_version","source","freshness",
              "live_orders_enabled","revision","quotes"}
    if (type(p) is not dict or set(p)!=required or
            p["protocol"]!="botking-v2-readonly" or
            type(p["schema_version"]) is not int or p["schema_version"]!=SCHEMA_VERSION or
            p["source"]!="dhan" or p["freshness"]!="unverified" or
            p["live_orders_enabled"] is not False or
            type(p["revision"]) is not int or p["revision"]<0 or
            type(p["quotes"]) is not dict):
        raise ContractError("Invalid V2 read-only snapshot")
    for sym,row in p["quotes"].items():
        if (not symbol_ok(sym) or type(row) is not dict or
                set(row)!={"price","freshness","live_verified","revision"} or
                type(row["price"]) not in (int,float) or
                not isfinite(row["price"]) or row["price"]<=0 or
                row["freshness"]!="unverified" or row["live_verified"] is not False or
                type(row["revision"]) is not int or row["revision"]<0 or
                row["revision"]>p["revision"]):
            raise ContractError("Invalid read-only quote")
    return p

def make_snapshot(revision,quotes):
    return validate_snapshot({"protocol":"botking-v2-readonly","schema_version":1,
                              "source":"dhan","freshness":"unverified",
                              "live_orders_enabled":False,
                              "revision":revision,"quotes":quotes})
