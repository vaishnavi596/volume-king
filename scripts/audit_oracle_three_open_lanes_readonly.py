#!/usr/bin/env python3
"""BOT KING remaining three release lanes: bounded local cache-only audit.

A = Options/Futures evidence, B = News/Four-factor scoring,
C = collector/snapshot age. Does not test CLOSED candle gates, send POST,
request Dhan, modify Oracle, log credentials, or claim live trading readiness.
Set BOTKING_AUDIT_PAIRING_KEY privately on Oracle before running.
"""
import json
import math
import os
import urllib.error
import urllib.request

ORIGIN = "http://127.0.0.1:8000"
SYMBOLS = ("NIFTY", "BANKNIFTY", "SENSEX")
ROUTES = ("/v2/server-readiness", "/v2/snapshot") + tuple(
    "/v2/assessment/" + s for s in SYMBOLS
)


def _number(x):
    return round(float(x), 2) if type(x) in (int, float) and math.isfinite(x) and x >= 0 else None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward a protected key through an HTTP redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _get(path, key):
    if path not in ROUTES:
        raise ValueError("Route outside bounded allowlist")
    if not key:
        return 0, {}
    request = urllib.request.Request(
        ORIGIN + path, method="GET",
        headers={"Accept": "application/json", "X-BotKing-Key": key},
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
    )
    try:
        with opener.open(request, timeout=5) as response:
            raw = response.read(131073)
            if len(raw) > 131072:
                return 0, {}
            value = json.loads(raw)
            return response.status, value if isinstance(value, dict) else {}
    except urllib.error.HTTPError as err:
        return err.code, {}
    except (urllib.error.URLError, OSError, ValueError):
        return 0, {}


def classify(readiness, snapshot, assessments):
    code, ready = readiness
    snap_code, snap = snapshot
    ready = ready if isinstance(ready, dict) else {}
    snap = snap if isinstance(snap, dict) else {}
    a = {}
    b = {}
    for symbol in SYMBOLS:
        http, data = assessments.get(symbol, (0, {}))
        data = data if isinstance(data, dict) else {}
        factors = data.get("factors")
        factors = factors if isinstance(factors, dict) else {}
        a[symbol] = {
            "http": http,
            "options": (factors.get("options") or {}).get("status") if isinstance(factors.get("options"), dict) else None,
            "futures": (factors.get("futures") or {}).get("status") if isinstance(factors.get("futures"), dict) else None,
            "filters_status": data.get("filters_status"),
            "cache_status": data.get("cache_status"),
        }
        b[symbol] = {
            "news": data.get("news_status"),
            "assessment_status": data.get("status"),
            "score_present": type(data.get("bullish_score")) in (int, float)
                             and type(data.get("bearish_score")) in (int, float)
                             and math.isfinite(data["bullish_score"]) and math.isfinite(data["bearish_score"]),
            "signal_eligible": data.get("signal_eligible") is True,
        }
    collector = ready.get("collector") if isinstance(ready.get("collector"), dict) else {}
    quotes = snap.get("quotes")
    c = {
        "readiness_http": code,
        "snapshot_http": snap_code,
        "collector_enabled": collector.get("configured_enabled"),
        "collector_status": collector.get("status"),
        "collection_interval_seconds": _number(collector.get("interval_seconds")),
        "last_success_age_seconds": _number(collector.get("last_success_age_seconds")),
        "snapshot_status": snap.get("collection_status"),
        "snapshot_age_seconds": _number(snap.get("age_seconds")),
        "cached_equity_count": len(quotes) if isinstance(quotes, dict) else None,
        "snapshot_orders_off": snap.get("live_orders_enabled") is False,
    }
    return {
        "lane_A_options_futures": a,
        "lane_B_news_scoring": {
            "indices": b,
            "readiness_news_status": (ready.get("news") or {}).get("status")
                                     if isinstance(ready.get("news"), dict) else None,
            "readiness_scoring_status": (ready.get("scoring") or {}).get("status")
                                        if isinstance(ready.get("scoring"), dict) else None,
        },
        "lane_C_collector_freshness": c,
        "notes": {
            "source": "Oracle cache-only GET, not independently exchange verified",
            "producer_post_executed": False,
            "direct_dhan_calls": 0,
            "source_edit": False,
            "live_orders_submitted": False,
            "apk_ready_asserted": False,
        },
    }


def main():
    key = os.environ.get("BOTKING_AUDIT_PAIRING_KEY", "").strip()
    if not key:
        print("AUTH_NOT_CONFIGURED: set BOTKING_AUDIT_PAIRING_KEY locally; never paste it")
        return
    response = {path: _get(path, key) for path in ROUTES}
    assessments = {
        s: response["/v2/assessment/" + s] for s in SYMBOLS
    }
    print(json.dumps(classify(response["/v2/server-readiness"],
                              response["/v2/snapshot"], assessments),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
