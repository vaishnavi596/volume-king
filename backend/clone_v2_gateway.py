"""Separate B2 clone-only Oracle login gateway, SSK authenticated and read-only.

Never reuse/deploy the old V2 pilot or modify the running V1 service.
Owner operates this on 127.0.0.1:8002 behind a reviewed HTTPS proxy. No
market quote/candle endpoints or broker trading orders are added here.
"""
from __future__ import annotations

import hmac
import json
import math
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone
import os
import stat
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

KEY_ENV = "BOTKING_CLONE_V2_SSK_FILE"
PROTOCOL = "botking-clone-v2"


def private_ssk(path):
    """Load an operator-protected key without exposing bytes in logs."""
    if (type(path) is not str or not path.startswith("/home/opc/")
            or not Path(path).is_absolute() or ".." in Path(path).parts):
        raise ValueError("Clone V2 private SSK path required")
    p = Path(path)
    if (p.is_symlink() or not p.is_file() or p.parent.is_symlink()
            or stat.S_IMODE(p.parent.stat().st_mode) & 0o077
            or stat.S_IMODE(p.stat().st_mode) & 0o077
            or p.stat().st_size < 32 or p.stat().st_size > 1024):
        raise ValueError("Clone V2 private SSK missing or unprotected")
    key = p.read_bytes().strip()
    if len(key) < 32 or len(key) > 512 or any(c < 33 or c > 126 for c in key):
        raise ValueError("Clone V2 SSK format invalid")
    return key




class MarketCandles(BaseModel):
    symbol: str
    interval: int
    from_date: date
    to_date: date


class MarketUnderlying(BaseModel):
    symbol: str


class MarketOptionChain(BaseModel):
    symbol: str
    expiry: date


class MarketRequest(BaseModel):
    symbols: list


def load_equity_registry(path):
    """Validate independently; never trust app-supplied security IDs."""
    try:
        target = Path(path)
        if target.is_symlink() or target.stat().st_size > 4_000_000:
            return {}
        obj = json.loads(target.read_text(encoding="utf-8"))
        entries = obj["equities"]
        if (obj.get("schema_version") != 1 or obj.get("source") != "dhan_instrument_master"
                or not isinstance(entries, dict) or not 300 <= len(entries) <= 10000
                or obj.get("equity_count") != len(entries)):
            return {}
        out, used = {}, set()
        for symbol, row in entries.items():
            sid = row.get("security_id") if isinstance(row, dict) else None
            if (not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9&_-]{1,32}", symbol)
                    or row.get("segment") != "NSE_EQ" or row.get("instrument") != "EQUITY"
                    or type(sid) is not int or sid <= 0 or sid in used):
                return {}
            used.add(sid)
            out[symbol] = ("NSE_EQ", sid)
        return out
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return {}


def create_app(*, key_bytes=None, market_feed_factory=None, market_registry=None):
    """Fail closed at startup if owner has not provisioned a protected key."""
    if key_bytes is None:
        key_bytes = private_ssk(os.environ.get(KEY_ENV))
    if (type(key_bytes) is not bytes or not 32 <= len(key_bytes) <= 512
            or any(c < 33 or c > 126 for c in key_bytes)):
        raise ValueError("Approved Clone V2 SSK required")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


    indices = {"NIFTY": ("IDX_I", 13), "BANKNIFTY": ("IDX_I", 25),
               "SENSEX": ("BSE_I", 51)}
    registry = (market_registry if market_registry is not None else
                load_equity_registry(os.environ.get("BOTKING_CLONE_DHAN_REGISTRY",
                "/opt/bot-king-backups/registry-audit/dhan_equity_registry.json")))
    known = dict(registry)
    known.update(indices)
    market_lock = threading.Lock()
    market_cache = {}
    last_request = [0.0]
    provider_cooldown_until = [0.0]

    def authorized(key):
        if (not isinstance(key, str) or len(key) > 1024
                or not hmac.compare_digest(key.encode("utf-8"), key_bytes)):
            raise HTTPException(403, "Clone V2 server access denied")

    def provider():
        if market_feed_factory is not None:
            return market_feed_factory()
        from dhan_feed import DhanFeed
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        location = os.environ.get("BOTKING_CLONE_DHAN_TOKEN_FILE", "")
        if not client or not location.startswith("/home/opc/"):
            raise HTTPException(503, "Clone Dhan credentials unavailable")
        target = Path(location)
        if (target.is_symlink() or not target.is_file()
                or stat.S_IMODE(target.stat().st_mode) & 0o077):
            raise HTTPException(503, "Clone Dhan token file unavailable")
        token = target.read_text(encoding="utf-8").strip()
        if not token:
            raise HTTPException(503, "Clone Dhan token unavailable")
        return DhanFeed(client, token)

    @app.get("/clone-v2/status")
    def status(x_botking_key: Optional[str] = Header(default=None)):
        # Constant-time authorization, including unknown or malformed keys.
        if (not isinstance(x_botking_key, str)
                or len(x_botking_key) > 1024
                or not hmac.compare_digest(
                    x_botking_key.encode("utf-8"), key_bytes)):
            raise HTTPException(403, "Clone V2 server access denied")
        return JSONResponse(
            {"protocol": PROTOCOL, "authenticated": True, "read_only": True,
             "live_orders_enabled": False, "pipeline": "dhan-oracle-clone",
             "status": "ready"},
            headers={"Cache-Control": "no-store"})

    @app.get("/clone-v2/health")
    def health():
        # Health is not proof of authorization or live market data.
        return JSONResponse(
            {"status": "gateway_process_ready", "live_data_verified": False,
             "live_orders_enabled": False},
            headers={"Cache-Control": "no-store"})


    @app.post("/clone-v2/market/quotes")
    def market_quotes(body: MarketRequest,
                      x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        symbols = body.symbols
        if (not isinstance(symbols, list) or not 1 <= len(symbols) <= 73
                or len(symbols) != len(set(s for s in symbols if isinstance(s, str)))
                or any(not isinstance(s, str) or s not in known for s in symbols)
                or sum(s not in indices for s in symbols) > 70):
            raise HTTPException(422, "Invalid or duplicate clone selection")
        selection = tuple(sorted(symbols))
        with market_lock:
            now = time.monotonic()
            cache = market_cache.get(selection)
            if cache and 0 <= now - cache[0] < 20:
                return JSONResponse(cache[1], headers={"Cache-Control": "no-store"})
            if now < provider_cooldown_until[0]:
                raise HTTPException(429, "Clone Dhan provider cooldown",
                                    headers={"Retry-After": "30"})
            if now - last_request[0] < 1.05:
                raise HTTPException(429, "Clone quote lane paced",
                                    headers={"Retry-After": "2"})
            last_request[0] = now
            try:
                result = provider().batch_ltp([known[s] for s in symbols])
            except HTTPException:
                raise
            except Exception as exc:
                try:
                    from .dhan_feed import DhanRateLimitError
                except ImportError:
                    from dhan_feed import DhanRateLimitError
                if isinstance(exc, DhanRateLimitError):
                    provider_cooldown_until[0] = time.monotonic() + 30
                    raise HTTPException(429, "Clone Dhan quota cooldown",
                                        headers={"Retry-After": "30"}) from None
                raise HTTPException(502, "Clone read-only Dhan quote unavailable") from None
            if not isinstance(result, dict) or result.get("status") != "success" or not isinstance(result.get("data"), dict):
                raise HTTPException(502, "Invalid clone Dhan quote response")
            quotes = {}
            for symbol in symbols:
                seg, sid = known[symbol]
                try:
                    raw = result["data"][seg][str(sid)]["last_price"]
                    if type(raw) not in (int, float) or not math.isfinite(raw) or raw <= 0:
                        continue
                    quotes[symbol] = {"symbol": symbol, "ltp": float(raw),
                                      "source": "dhan", "freshness": "unverified"}
                except (KeyError, TypeError, ValueError, OverflowError):
                    pass
            if not quotes:
                raise HTTPException(502, "No validated clone quotes")
            payload = {"source": "dhan", "quotes": quotes,
                       "unavailable": [s for s in symbols if s not in quotes],
                       "freshness": "unverified", "live_orders_enabled": False}
            market_cache[selection] = (time.monotonic(), payload)
            # Share repeated selections across 1–4 phones, bounded by demand.
            if len(market_cache) > 16:
                market_cache.pop(min(market_cache, key=lambda k: market_cache[k][0]))
            return JSONResponse(payload, headers={"Cache-Control": "no-store"})


    @app.post("/clone-v2/market/verify")
    def market_verify(body: MarketUnderlying,
                      x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if body.symbol not in registry:
            raise HTTPException(422, "Clone equity mapping not verified")
        return JSONResponse({"symbol": body.symbol, "source": "dhan_registry",
                             "verified": True, "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/candles")
    def market_candles(body: MarketCandles,
                       x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if (body.symbol not in known or body.interval not in (1, 5, 15, 25, 60)
                or body.from_date > body.to_date
                or (body.to_date - body.from_date).days > 5
                or body.to_date > datetime.now(timezone(timedelta(hours=5, minutes=30))).date()):
            raise HTTPException(422, "Invalid Clone Dhan candle selection")
        segment, sid = known[body.symbol]
        instrument = "INDEX" if body.symbol in indices else "EQUITY"
        args = {"securityId": str(sid), "exchangeSegment": segment,
                "instrument": instrument, "interval": str(body.interval),
                "fromDate": body.from_date.isoformat() + " 09:15:00",
                "toDate": (body.to_date + timedelta(days=1)).isoformat() + " 00:00:00"}
        try:
            result = provider().intraday(args)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(502, "Clone Dhan candles unavailable") from None
        try:
            fields = ["timestamp", "open", "high", "low", "close", "volume"]
            arrays = [result[key] for key in fields]
            if (result.get("status") == "failure" or
                    any(not isinstance(v, list) for v in arrays) or
                    any(len(a) != len(arrays[0]) for a in arrays) or
                    len(arrays[0]) > 5000):
                raise ValueError()
            bars = []
            for ts, op, high, low, close, vol in zip(*arrays):
                if any(type(v) not in (int, float) for v in (ts, op, high, low, close, vol)):
                    raise ValueError()
                vals = (float(ts), float(op), float(high), float(low), float(close), float(vol))
                if (not all(math.isfinite(v) for v in vals) or ts <= 0
                        or min(op, high, low, close) <= 0 or vol < 0
                        or high < max(op, low, close) or low > min(op, high, close)):
                    raise ValueError()
                bars.append([int(ts), float(op), float(high), float(low),
                             float(close), float(vol)])
            if any(bars[i][0] >= bars[i + 1][0] for i in range(len(bars)-1)):
                raise ValueError()
        except (KeyError, TypeError, ValueError, OverflowError):
            raise HTTPException(502, "Clone Dhan candle response invalid") from None
        return JSONResponse({
            "source": "dhan", "symbol": body.symbol,
            "interval": str(body.interval) + "m", "bars": bars,
            "last_candle_timestamp": bars[-1][0] if bars else None,
            "freshness": "historical_unverified" if bars else "no_candles_available",
            "live_orders_enabled": False}, headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/options/expiries")
    def market_option_expiries(body: MarketUnderlying,
                               x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if body.symbol not in known or known[body.symbol][0] not in ("IDX_I", "BSE_I", "NSE_EQ"):
            raise HTTPException(422, "Unmapped Clone option underlying")
        try:
            dates = provider().option_expiries(*known[body.symbol])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(502, "Clone Dhan option expiry unavailable") from None
        if not isinstance(dates, list) or not dates:
            raise HTTPException(422, "No verified Clone listed expiry")
        return JSONResponse({"source": "dhan", "symbol": body.symbol,
                             "expiries": dates, "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/options/chain")
    def market_option_chain(body: MarketOptionChain,
                            x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if (body.symbol not in known or
                known[body.symbol][0] not in ("IDX_I", "BSE_I", "NSE_EQ") or
                body.expiry < datetime.now(timezone(timedelta(hours=5, minutes=30))).date()):
            raise HTTPException(422, "Invalid Clone option underlying or expiry")
        try:
            try:
                from .dhan_option_metrics import (calculate_option_metrics, listed_atm_window,
                                                  OptionMetricsUnavailable)
            except ImportError:
                from dhan_option_metrics import (calculate_option_metrics, listed_atm_window,
                                                 OptionMetricsUnavailable)
            raw = provider().option_chain(*known[body.symbol], body.expiry.isoformat())
            metrics = calculate_option_metrics(raw)
            raw_data = raw.get("data", {})
            spot = raw_data.get("last_price") if isinstance(raw_data, dict) else None
            window, window_status = None, "underlying_spot_unavailable"
            if type(spot) in (int, float) and math.isfinite(spot) and spot > 0:
                window_status = "listed_window_unavailable"
                try:
                    window = listed_atm_window(raw, spot=spot)
                    window_status = "available"
                except OptionMetricsUnavailable:
                    pass
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(502, "Clone Dhan option chain unavailable") from None
        return JSONResponse({"source": "dhan", "symbol": body.symbol,
                             "expiry": body.expiry.isoformat(), **metrics,
                             "atm_window": window, "atm_window_status": window_status,
                             "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    return app
