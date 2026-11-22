#!/usr/bin/env python3
"""Classify an existing V3 phone Doctor JSON report without any network requests.

Usage: python ops/v3_phone_index_acceptance_20261122.py report.json
No credentials, HTTP calls, or trading actions. Fail closed on absent evidence.
"""
import json
import sys
from pathlib import Path

INDEX = ("NIFTY", "BANKNIFTY", "SENSEX")
STAGES = {"PROVIDER_QUOTA", "PROVIDER_COOLDOWN"}


def assess(report):
    if not isinstance(report, dict):
        raise ValueError("Expected JSON object")
    result = {"test": "V3_S3_PHONE_INDEX_ACCEPTANCE", "mode": "OFFLINE_READ_ONLY",
              "orders_sent": 0, "indices": {}, "overall": "NOT_VERIFIED"}
    quotes = report.get("quotes")
    if not isinstance(quotes, dict):
        quotes = {}
    for symbol in INDEX:
        item = quotes.get(symbol)
        price = item.get("ltp") if isinstance(item, dict) else None
        valid = type(price) in (int, float) and 0 < price < float("inf")
        result["indices"][symbol] = "PRICE_PRESENT_UNVERIFIED_FRESHNESS" if valid else "MISSING_OR_INVALID"
    stage = report.get("index_failure_code") or report.get("429_stage")
    result["429_stage"] = stage if stage in STAGES else "NOT_CONFIRMED"
    result["freshness"] = "NOT_VERIFIED"
    result["provider_source"] = "NOT_VERIFIED"
    result["overall"] = "PRICES_PRESENT_ONLY" if all(
        value == "PRICE_PRESENT_UNVERIFIED_FRESHNESS" for value in result["indices"].values()
    ) else "INCOMPLETE"
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python ops/v3_phone_index_acceptance_20261122.py report.json")
    path = Path(sys.argv[1])
    if path.stat().st_size > 1_000_000:
        raise SystemExit("Report too large")
    report = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(assess(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
