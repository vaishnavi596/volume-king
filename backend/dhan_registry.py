"""Strict read-only Dhan Equity Registry loader.

The staged instrument-master JSON is NOT an entitlement or a live quote.
On any malformed or conflicting registry, retain the known 51-equity baseline.
No filesystem writes, Dhan requests, or broker orders.
"""
import json
import logging
import re
from pathlib import Path

DEFAULT_REGISTRY = Path("/opt/bot-king-backups/registry-audit/dhan_equity_registry.json")
_SYMBOL = re.compile(r"^[A-Z0-9&_-]{1,32}$")


def load_dynamic_instruments(legacy, path=DEFAULT_REGISTRY):
    result = dict(legacy)
    try:
        path = Path(path)
        if path.stat().st_size > 4_000_000:
            raise ValueError("Equity registry exceeds bound")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError("Incorrect registry schema")
        if data.get("source") != "dhan_instrument_master":
            raise ValueError("Unknown registry provenance")
        items = data.get("equities")
        if not isinstance(items, dict) or not 300 <= len(items) <= 10000:
            raise ValueError("Incorrect registry count")
        if type(data.get("equity_count")) is not int or data["equity_count"] != len(items):
            raise ValueError("Registry count mismatch")
        additions = {}
        ids = set()
        for sym, item in items.items():
            if not isinstance(sym, str) or not _SYMBOL.fullmatch(sym):
                raise ValueError("Invalid registry symbol")
            if (not isinstance(item, dict) or item.get("segment") != "NSE_EQ"
                    or item.get("instrument") != "EQUITY"):
                raise ValueError("Invalid equity descriptor")
            sid = item.get("security_id")
            if type(sid) is not int or sid <= 0 or sid in ids:
                raise ValueError("Duplicate or invalid security ID")
            ids.add(sid)
            mapped = ("NSE_EQ", sid, "EQUITY")
            if sym in result and result[sym] != mapped:
                raise ValueError("Legacy symbol conflict")
            additions[sym] = mapped
        result.update(additions)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        logging.getLogger("botking.registry").warning(
            "Registry unavailable; retained verified baseline (%s)", type(exc).__name__)
    return result
