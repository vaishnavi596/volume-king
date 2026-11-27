"""Separate B2 clone-only Oracle login gateway, SSK authenticated and read-only.

Never reuse/deploy the old V2 pilot or modify the running V1 service.
Owner operates this on 127.0.0.1:8002 behind a reviewed HTTPS proxy. No
market quote/candle endpoints or broker trading orders are added here.
"""
from __future__ import annotations
import hashlib

import hmac
import secrets
import tempfile
import urllib.parse
import urllib.request
import urllib.error
import json
import logging
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
from fastapi.responses import JSONResponse, HTMLResponse

KEY_ENV = "BOTKING_CLONE_V2_SSK_FILE"
PROTOCOL = "botking-clone-v2"
DIAGNOSTIC_LOGGER = logging.getLogger("botking.clone.market")


def observed_trade_timestamp(value, *, now):
    """Dhan quote wall-clock IST; reject placeholders/future values, not old HIST.
    A trade timestamp is not a verified candle or independent LIVE vote.
    """
    if not isinstance(value, str):
        return None
    # Official quote examples use DD/MM/YYYY; retain legacy ISO wall time.
    # Neither the HTTP arrival time nor a placeholder is a trade timestamp.
    if type(now) not in (int,float) or not math.isfinite(now):
        return None
    for fmt, pattern in (
        ("%d/%m/%Y %H:%M:%S", r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"),
        ("%Y-%m-%d %H:%M:%S", r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"),
    ):
        if not re.fullmatch(pattern, value, flags=re.ASCII):
            continue
        try:
            stamp = datetime.strptime(value, fmt).replace(
                tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp()
            return stamp if 946684800 <= stamp <= now else None
        except (ValueError, OverflowError, OSError):
            return None
    return None


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


class MarketFuturesContext(BaseModel):
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


def regular_session_now():
    """True during NSE regular hours (IST weekdays 09:15-15:35)."""
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    return ist.weekday() < 5 and (9, 15) <= (ist.hour, ist.minute) < (15, 35)


def create_app(*, key_bytes=None, market_feed_factory=None, market_registry=None,
               consent_config_factory=None, futures_master_factory=None):
    """Fail closed at startup if owner has not provisioned a protected key."""
    if key_bytes is None:
        key_bytes = private_ssk(os.environ.get(KEY_ENV))
    if (type(key_bytes) is not bytes or not 32 <= len(key_bytes) <= 512
            or any(c < 33 or c > 126 for c in key_bytes)):
        raise ValueError("Approved Clone V2 SSK required")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


    indices = {"NIFTY": ("IDX_I", 13), "BANKNIFTY": ("IDX_I", 25),
               "SENSEX": ("IDX_I", 51)}
    registry = (market_registry if market_registry is not None else
                load_equity_registry(os.environ.get("BOTKING_CLONE_DHAN_REGISTRY",
                "/opt/bot-king-backups/registry-audit/dhan_equity_registry.json")))
    known = dict(registry)
    known.update(indices)
    # FINNIFTY is an options underlying (Dhan IDX_I/27), not a fourth
    # dashboard index. Keep it out of the three-index quote/candle lanes.
    option_known = dict(known)
    option_known["FINNIFTY"] = ("IDX_I", 27)
    market_lock = threading.Lock()
    market_cache = {}
    last_request = [0.0]
    provider_cooldown_until = [0.0]
    quota_lock = threading.Lock()

    def quota_remaining():
        with quota_lock:
            return max(0.0, provider_cooldown_until[0] - time.monotonic())

    def quota_start(seconds=30):
        with quota_lock:
            provider_cooldown_until[0] = max(
                provider_cooldown_until[0], time.monotonic() + seconds)

    def quota_guard():
        remaining = quota_remaining()
        if remaining > 0:
            raise HTTPException(429, "Clone Dhan provider cooldown",
                headers={"Retry-After": str(max(1, math.ceil(remaining))),
                         "X-BotKing-429-Stage": "PROVIDER_COOLDOWN"})

    def quota_error(exc):
        try:
            from .dhan_feed import DhanLocalPacingError, DhanCooldownError
        except ImportError:
            from dhan_feed import DhanLocalPacingError, DhanCooldownError
        if isinstance(exc, DhanLocalPacingError):
            stage, seconds = "LOCAL_PACING", exc.retry_seconds
        elif isinstance(exc, DhanCooldownError):
            stage, seconds = "PROVIDER_COOLDOWN", exc.retry_seconds
        else:
            quota_start()
            stage, seconds = "PROVIDER_QUOTA", 30
        raise HTTPException(429, "Clone Dhan request deferred",
            headers={"Retry-After": str(seconds),
                     "X-BotKing-429-Stage": stage}) from None
    # Clone-owned candle single-flight and validated, date-scoped history cache.
    # Kept independent of V1 server and files; only successful nonempty bars.
    candle_cache = {}
    candle_cache_lock = threading.RLock()
    candle_miss_locks = tuple(threading.RLock() for _ in range(32))
    candle_cache_ttl_seconds = 180
    candle_cache_max_entries = 100

    def candle_cache_current(entry, interval, to_date, now=None):
        """During regular hours a cached response is reusable only while it
        still holds the newest CLOSED bar (live qualification needs the last
        completed bar <=90 s old). Outside hours the plain TTL applies."""
        now = time.time() if now is None else now
        ist = datetime.fromtimestamp(now, timezone(timedelta(hours=5, minutes=30)))
        if len(entry) < 3 or to_date != ist.date() or ist.weekday() > 4:
            return True
        opening = ist.replace(hour=9, minute=15, second=0, microsecond=0).timestamp()
        if not opening <= now < opening + 6 * 3600 + 20 * 60:
            return True
        width = int(interval) * 60
        grace = 4
        boundary = opening + ((now - opening) // width) * width
        if now - boundary < grace:
            boundary -= width
        if entry[2] < boundary + grace:
            return False
        last = entry[1].get("last_candle_timestamp")
        if (type(last) in (int, float) and last < boundary - width
                and now - entry[2] >= 5):
            return False
        return True

    def market_diagnostic(route, symbol, stage, category):
        """Fixed-enum diagnostics for mapped symbols; no payloads or credentials."""
        if (route not in ("quotes", "candles", "option_expiries", "option_chain")
                or symbol not in option_known
                or stage not in ("provider", "shape", "mapping", "validation", "cooldown")
                or category not in ("missing_segment", "missing_security_id",
                                    "invalid_price", "invalid_shape", "invalid_bars",
                                    "rate_limited", "auth_unavailable", "upstream_error",
                                    "upstream_http_4xx", "upstream_http_5xx",
                                    "upstream_transport", "upstream_payload",
                                    "upstream_rejection")):
            return
        DIAGNOSTIC_LOGGER.warning(
            "clone_market_diagnostic route=%s symbol=%s stage=%s category=%s",
            route, symbol, stage, category)

    # Clone-owned, optional browser-consent flow; NEVER borrow V1's HTTP auth.
    # Server must have a separately approved Dhan callback pointing here.
    consent_lock = threading.RLock()
    consent_pending = {"until": 0.0, "active": False}
    consent_cooldown_until = [0.0]

    def clone_oauth_config():
        if consent_config_factory is not None:
            return consent_config_factory()
        # Owner has retired V1 as a target app. Reuse its registered Dhan OAuth
        # redirect under an EXPLICIT Clone-only cutover setting. Changing the
        # broker developer-app callback or generating another app is unnecessary.
        if os.environ.get("BOTKING_CLONE_DHAN_CALLBACK_APPROVED") != "1":
            raise HTTPException(503, "Clone Dhan callback handoff not approved")
        callback = os.environ.get("BOTKING_CLONE_DHAN_CALLBACK_URL", "")
        expected = "https://botkingrajesh.duckdns.org/dhan/callback"
        if callback != expected:
            raise HTTPException(503, "Registered V1 callback handoff not configured")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        app_id = os.environ.get("BOTKING_CLONE_DHAN_APP_ID", "").strip()
        secret = os.environ.get("BOTKING_CLONE_DHAN_APP_SECRET", "").strip()
        location = os.environ.get("BOTKING_CLONE_DHAN_TOKEN_FILE", "")
        if (not client or not app_id or not secret or
                not location.startswith("/home/opc/")):
            raise HTTPException(503, "Clone Dhan browser authorization not configured")
        return client, app_id, secret, Path(location)

    def clone_token_path(target):
        if (target.is_symlink() or not target.is_file() or
                stat.S_IMODE(target.stat().st_mode) & 0o077 or
                target.stat().st_uid != os.geteuid()):
            raise HTTPException(503, "Clone token storage is not secure")

    class NoBrokerRedirect(urllib.request.HTTPRedirectHandler):
        # Never forward any broker app secret or access token through a redirect.
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def broker_json(request):
        try:
            with urllib.request.build_opener(
                urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(),
                NoBrokerRedirect()
            ).open(request, timeout=15) as response:
                if response.status != 200:
                    raise ValueError("Bad broker response")
                payload = response.read(100001)
            if len(payload) > 100000:
                raise ValueError("Oversized broker response")
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise ValueError("Invalid broker response")
            return data
        except (urllib.error.URLError, OSError, ValueError, UnicodeError):
            raise HTTPException(502, "Dhan browser authorization unavailable") from None

    @app.post("/clone-v2/dhan/start")
    def clone_dhan_start(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        client, app_id, secret, target = clone_oauth_config()
        clone_token_path(target)
        with consent_lock:
            now = time.monotonic()
            if consent_pending["active"] and now < consent_pending["until"]:
                raise HTTPException(409, "Clone Dhan login already pending")
            if now < consent_cooldown_until[0]:
                raise HTTPException(429, "Clone consent request paced")
            consent_cooldown_until[0] = now + 8
            request = urllib.request.Request(
                "https://auth.dhan.co/app/generate-consent?"+
                urllib.parse.urlencode({"client_id": client}),
                headers={"app_id": app_id, "app_secret": secret,
                         "Accept": "application/json"},
                data=b"", method="POST")
            result = broker_json(request)
            consent = result.get("consentAppId")
            if not isinstance(consent, str) or not 1 <= len(consent) <= 200:
                raise HTTPException(502, "Dhan consent ID unavailable")
            consent_pending.update(active=True, until=time.monotonic()+300)
        login_url = ("https://auth.dhan.co/login/consentApp-login?"+
                     urllib.parse.urlencode({"consentAppId": consent}))
        return JSONResponse(
            {"login_url": login_url, "expires_in": 300,
             "live_orders_enabled": False}, headers={"Cache-Control": "no-store"})

    # Exact legacy Dhan redirect accepted by Clone only after HTTPS cutover.
    # Nginx exact-match /dhan/callback must route here, NOT V1 port 8000.
    @app.get("/dhan/callback", response_class=HTMLResponse)
    @app.get("/clone-v2/dhan/callback", response_class=HTMLResponse)
    def clone_dhan_callback(tokenId: Optional[str] = None):
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
        with consent_lock:
            now=time.monotonic()
            if not consent_pending["active"] or now >= consent_pending["until"]:
                raise HTTPException(403, "No active Clone Dhan authorization")
            # Single use, including failure: never replay tokenIds.
            consent_pending.update(active=False, until=0.0)
            if not isinstance(tokenId, str) or not 1 <= len(tokenId) <= 2048:
                raise HTTPException(400, "Invalid Dhan callback")
            client, app_id, secret, target = clone_oauth_config()
            clone_token_path(target)
            url=("https://auth.dhan.co/app/consumeApp-consent?"+
                 urllib.parse.urlencode({"tokenId": tokenId}))
            request=urllib.request.Request(url, headers={
                "app_id":app_id, "app_secret":secret, "Accept":"application/json"
            }, method="GET")
            result=broker_json(request)
            new_token=result.get("accessToken")
            expiry=result.get("expiryTime")
            if (not isinstance(new_token, str) or len(new_token) < 20
                    or str(result.get("dhanClientId")) != client):
                raise HTTPException(502, "Dhan authenticated account mismatch")
            try:
                from zoneinfo import ZoneInfo
                dt=datetime.fromisoformat(str(expiry).replace("Z","+00:00"))
                if dt.tzinfo is None:
                    dt=dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                if dt.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                    raise ValueError()
            except (ValueError, TypeError, OverflowError):
                raise HTTPException(502, "Dhan token expiry not verified") from None
            # Dhan callback success alone is not verified market permission.
            # Validate the new token against the official profile before replacing.
            verified=broker_json(urllib.request.Request(
                "https://api.dhan.co/v2/profile",
                headers={"access-token":new_token, "Accept":"application/json"},
                method="GET"))
            if str(verified.get("dhanClientId")) != client:
                raise HTTPException(502,"New Dhan token profile/account unverified")
            if str(verified.get("dataPlan","")).lower() != "active":
                raise HTTPException(424,"Dhan market-data subscription not active")
            # Atomic clone-private write; V1 token and V1 OAuth are untouched.
            temp=None
            st=target.stat()
            try:
                fd,temp=tempfile.mkstemp(prefix=".clone-dhan-token-", dir=str(target.parent))
                os.fchmod(fd, 0o600)
                os.fchown(fd, st.st_uid, st.st_gid)
                with os.fdopen(fd,"w",encoding="utf-8") as out:
                    out.write(new_token+chr(10))
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temp,target)
                temp=None
                directory_fd=os.open(str(target.parent),os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                raise HTTPException(503,"Clone private Dhan session could not be saved") from None
            finally:
                if temp is not None:
                    Path(temp).unlink(missing_ok=True)
        return HTMLResponse(
            "<!doctype html><html><head><meta name='referrer' content='no-referrer'></head>"+
            "<body><h2>BOT KING Clone: Dhan login successful</h2>"+
            "<p>Return to BOT KING Clone and press Connect Clone V2 (SSK). "+
            "Trading orders remain disabled.</p></body></html>",
            headers=headers)


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

    @app.get("/clone-v2/renewal-health")
    def renewal_health(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        # Explicitly provisioned metadata only. No token read, Dhan request,
        # timer execution, credential mutation or inference of renewal success.
        try:
            from .dhan_renewal_health import renewal_health_report
        except ImportError:
            from dhan_renewal_health import renewal_health_report
        return JSONResponse(renewal_health_report(
            os.environ.get("BOTKING_CLONE_RENEWAL_EXPIRY_FILE")),
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
            # Only a COMPLETE three-index batch gets V1-parity 60s reuse.
            # Incomplete SENSEX/BANKNIFTY/NIFTY batches keep 20s recovery.
            full_index_batch = selection == tuple(sorted(indices))
            cache_ttl = (60 if full_index_batch and cache
                         and not cache[1].get("unavailable") else 20)
            # Regular hours: live qualification needs a last-trade stamp no
            # older than the newest completed bar, so reuse is capped at 10 s.
            if full_index_batch and regular_session_now():
                cache_ttl = min(cache_ttl, 10)
            if cache and 0 <= now - cache[0] < cache_ttl:
                return JSONResponse(cache[1], headers={"Cache-Control": "no-store"})
            if quota_remaining() > 0:
                for sym in symbols:
                    market_diagnostic("quotes", sym, "cooldown", "rate_limited")
                quota_guard()
            # Queue legitimate authenticated quote selections inside the
            # existing server-wide lock instead of returning a spurious 429
            # when two phones/index/equity lanes arrive within 1.05 seconds.
            # Still issue at most one upstream batch per 1.05s and keep the
            # independent provider quota 429/30s cooldown fail-closed.
            spacing_remaining=1.05-(now-last_request[0])
            if 0 < spacing_remaining <= 1.05:
                time.sleep(spacing_remaining)
                now=time.monotonic()
                quota_guard()
            last_request[0] = now
            try:
                feed = provider()
                # One request, same quota gate. Legacy injected feeds remain LTP-only.
                quote_reader = getattr(feed, "batch_quote", None)
                result = (quote_reader if callable(quote_reader) else feed.batch_ltp)([known[s] for s in symbols])
            except HTTPException:
                raise
            except Exception as exc:
                try:
                    from .dhan_feed import DhanRateLimitError, DhanFeedError
                except ImportError:
                    from dhan_feed import DhanRateLimitError, DhanFeedError
                if (isinstance(exc, DhanFeedError) and
                        "token expired or data access not entitled" in str(exc)):
                    category="auth_unavailable"
                elif isinstance(exc, DhanRateLimitError):
                    category="rate_limited"
                else:
                    category=getattr(exc, "category", "upstream_error")
                    if category not in ("upstream_http_4xx", "upstream_http_5xx",
                                        "upstream_transport", "upstream_payload",
                                        "upstream_rejection", "upstream_error"):
                        category="upstream_error"
                for sym in symbols:
                    market_diagnostic("quotes", sym, "provider", category)
                if category=="auth_unavailable":
                    raise HTTPException(
                        424, "Dhan browser authorization or data permission required") from None
                if category=="rate_limited":
                    quota_error(exc)
                raise HTTPException(502, "Clone read-only Dhan quote unavailable",
                                    headers={"X-BotKing-Quote-Failure-Stage": "PROVIDER"}) from None
            if not isinstance(result, dict) or result.get("status") != "success" or not isinstance(result.get("data"), dict):
                for sym in symbols:
                    market_diagnostic("quotes", sym, "shape", "invalid_shape")
                raise HTTPException(502, "Invalid clone Dhan quote response",
                                    headers={"X-BotKing-Quote-Failure-Stage": "RESPONSE"})
            quotes = {}
            for symbol in symbols:
                seg, sid = known[symbol]
                segment_data=result["data"].get(seg)
                if not isinstance(segment_data, dict):
                    market_diagnostic("quotes", symbol, "mapping", "missing_segment")
                elif not isinstance(segment_data.get(str(sid)), dict):
                    market_diagnostic("quotes", symbol, "mapping", "missing_security_id")
                try:
                    raw = result["data"][seg][str(sid)]["last_price"]
                    if type(raw) not in (int, float) or not math.isfinite(raw) or raw <= 0:
                        market_diagnostic("quotes", symbol, "validation", "invalid_price")
                        continue
                    quotes[symbol] = {"symbol": symbol, "ltp": float(raw),
                                      "source": "dhan", "freshness": "unverified"}
                    if callable(quote_reader):
                        # B248: day change % from Dhan quote net_change (prev close = ltp - net_change).
                        nc = result["data"][seg][str(sid)].get("net_change")
                        if type(nc) in (int, float) and math.isfinite(nc):
                            prev = float(raw) - float(nc)
                            if prev > 0 and abs(nc / prev * 100) <= 50:
                                quotes[symbol]["change_pct"] = round(nc / prev * 100, 4)
                        stamp = observed_trade_timestamp(result["data"][seg][str(sid)].get("last_trade_time"), now=time.time())
                        if stamp is not None:
                            quotes[symbol].update(exchange_trade_timestamp=stamp,
                                timestamp_origin="DHAN_QUOTE_LAST_TRADE_TIME")
                except (KeyError, TypeError, ValueError, OverflowError):
                    if isinstance(segment_data, dict) and isinstance(segment_data.get(str(sid)), dict):
                        market_diagnostic("quotes", symbol, "validation", "invalid_price")
            if not quotes:
                # An HTTP-success Dhan payload containing empty segment objects
                # is not valid quote proof. Bound repeated upstream retries.
                # Do not substitute last-good/HIST prices or fabricated LIVE data.
                empty_segments = all(
                    isinstance(result["data"].get(known[sym][0]), dict)
                    and not result["data"][known[sym][0]]
                    for sym in symbols
                )
                if empty_segments:
                    quota_start()
                    raise HTTPException(502, "No validated clone quotes",
                                        headers={"Retry-After": "30",
                                                 "X-BotKing-Quote-Failure-Stage": "RESPONSE",
                                                 "X-BotKing-Quote-Response-State": "EMPTY_SEGMENTS"})
                raise HTTPException(502, "No validated clone quotes",
                                    headers={"X-BotKing-Quote-Failure-Stage": "RESPONSE"})
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

    def provider_read_error(exc, unavailable_message):
        """Classify provider throttling without exposing credentials or responses."""
        try:
            from .dhan_feed import DhanRateLimitError, DhanFeedError
        except ImportError:
            from dhan_feed import DhanRateLimitError, DhanFeedError
        if isinstance(exc, DhanRateLimitError):
            quota_error(exc)
        if (isinstance(exc, DhanFeedError) and
                "token expired or data access not entitled" in str(exc)):
            raise HTTPException(
                424, "Dhan browser authorization or data permission required") from None
        raise HTTPException(502, unavailable_message) from None


    @app.post("/clone-v2/market/candles")
    def market_candles(body: MarketCandles,
                       x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if (body.symbol not in known or body.interval not in (1, 5, 15, 25, 60)
                or body.from_date > body.to_date
                or (body.to_date - body.from_date).days > 5
                or body.to_date > datetime.now(timezone(timedelta(hours=5, minutes=30))).date()):
            raise HTTPException(422, "Invalid Clone Dhan candle selection")
        cache_key = (body.symbol, body.interval, body.from_date, body.to_date)
        # A lock stripe coalesces concurrent same-request misses across 1–4 phones.
        # Recheck inside lock so only one provider fetch runs for a matching key.
        miss_lock = candle_miss_locks[hash(cache_key) % len(candle_miss_locks)]
        with miss_lock:
            with candle_cache_lock:
                cached = candle_cache.get(cache_key)
                if (cached and 0 <= time.monotonic() - cached[0] < candle_cache_ttl_seconds
                        and candle_cache_current(cached, body.interval, body.to_date)):
                    return JSONResponse(cached[1], headers={"Cache-Control": "no-store"})
            segment, sid = known[body.symbol]
            instrument = "INDEX" if body.symbol in indices else "EQUITY"
            args = {"securityId": str(sid), "exchangeSegment": segment,
                    "instrument": instrument, "interval": str(body.interval),
                    "fromDate": body.from_date.isoformat() + " 09:15:00",
                    "toDate": (body.to_date + timedelta(days=1)).isoformat() + " 00:00:00"}
            try:
                quota_guard()
                result = provider().intraday(args)
            except HTTPException:
                raise
            except Exception as exc:
                try:
                    from .dhan_feed import DhanRateLimitError, DhanFeedError
                except ImportError:
                    from dhan_feed import DhanRateLimitError, DhanFeedError
                category=("rate_limited" if isinstance(exc, DhanRateLimitError)
                          else "auth_unavailable" if isinstance(exc, DhanFeedError)
                          and "token expired or data access not entitled" in str(exc)
                          else getattr(exc, "category", "upstream_error"))
                if category not in ("rate_limited", "auth_unavailable",
                                    "upstream_http_4xx", "upstream_http_5xx",
                                    "upstream_transport", "upstream_payload",
                                    "upstream_rejection", "upstream_error"):
                    category="upstream_error"
                market_diagnostic("candles", body.symbol, "provider", category)
                provider_read_error(exc, "Clone Dhan candles unavailable")
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
                market_diagnostic("candles", body.symbol, "validation", "invalid_bars")
                raise HTTPException(502, "Clone Dhan candle response invalid") from None
            payload = {
                "source": "dhan", "symbol": body.symbol,
                "interval": str(body.interval) + "m", "bars": bars,
                "candle_origin": "DHAN_INTRADAY_TIMESTAMP",
                "last_candle_timestamp": bars[-1][0] if bars else None,
                # Hash of normalized broker OHLCV after shape validation.
                # It verifies transport equality only, never exchange freshness.
                "normalized_bars_sha256": hashlib.sha256(
                    json.dumps(bars, separators=(",",":"), allow_nan=False).encode("utf-8")
                ).hexdigest(),
                "freshness": "historical_unverified" if bars else "no_candles_available",
                "live_orders_enabled": False}
            if bars:
                with candle_cache_lock:
                    candle_cache[cache_key] = (time.monotonic(), payload, time.time())
                    if len(candle_cache) > candle_cache_max_entries:
                        candle_cache.pop(min(candle_cache, key=lambda k: candle_cache[k][0]))
            return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/futures/context")
    def market_futures_context(body: MarketFuturesContext,
                               x_botking_key: Optional[str] = Header(default=None)):
        """Mapped read-only NSE_FNO LTP. This is context, never a directional vote."""
        authorized(x_botking_key)
        ist_today=datetime.now(timezone(timedelta(hours=5,minutes=30))).date()
        if body.symbol not in known or body.expiry < ist_today:
            raise HTTPException(422,"Unknown or expired futures underlying")
        # No operator-validated Dhan futures master means NO provider call.
        if futures_master_factory is None:
            raise HTTPException(503,"Dhan futures instrument master not provisioned")
        try:
            try:
                from .futures_context import select_verified_future, normalize_futures_ltp
            except ImportError:
                from futures_context import select_verified_future, normalize_futures_ltp
            rows=futures_master_factory()
            mapped=select_verified_future(rows,body.symbol,body.expiry)
        except (TypeError,ValueError,KeyError):
            mapped=None
        if mapped is None:
            raise HTTPException(422,"Unique verified Dhan futures contract unavailable")
        with market_lock:
            now=time.monotonic()
            quota_guard()
            remain=1.05-(now-last_request[0])
            if 0 < remain <= 1.05:
                time.sleep(remain)
                quota_guard()
            last_request[0]=time.monotonic()
            try:
                raw=provider().ltp("NSE_FNO",mapped["security_id"])
            except HTTPException:
                raise
            except Exception as exc:
                try:
                    from .dhan_feed import DhanRateLimitError
                except ImportError:
                    from dhan_feed import DhanRateLimitError
                if isinstance(exc,DhanRateLimitError):
                    quota_error(exc)
                raise HTTPException(502,"Dhan futures quote unavailable") from None
        context=normalize_futures_ltp(raw,mapped)
        if context is None:
            raise HTTPException(502,"Dhan futures quote shape unverified")
        return JSONResponse(context,headers={"Cache-Control":"no-store"})

    @app.post("/clone-v2/market/options/expiries")
    def market_option_expiries(body: MarketUnderlying,
                               x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if body.symbol not in option_known or option_known[body.symbol][0] not in ("IDX_I", "BSE_I", "NSE_EQ"):
            raise HTTPException(422, "Unmapped Clone option underlying")
        try:
            quota_guard()
            dates = provider().option_expiries(*option_known[body.symbol])
        except HTTPException:
            raise
        except Exception as exc:
            provider_read_error(exc, "Clone Dhan option expiry unavailable")
        if not isinstance(dates, list) or not dates:
            raise HTTPException(422, "No verified Clone listed expiry")
        return JSONResponse({"source": "dhan", "symbol": body.symbol,
                             "expiries": dates, "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/options/chain")
    def market_option_chain(body: MarketOptionChain,
                            x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if (body.symbol not in option_known or
                option_known[body.symbol][0] not in ("IDX_I", "BSE_I", "NSE_EQ") or
                body.expiry < datetime.now(timezone(timedelta(hours=5, minutes=30))).date()):
            raise HTTPException(422, "Invalid Clone option underlying or expiry")
        try:
            try:
                from .dhan_option_metrics import (calculate_option_metrics, listed_atm_window,
                                                  OptionMetricsUnavailable)
            except ImportError:
                from dhan_option_metrics import (calculate_option_metrics, listed_atm_window,
                                                 OptionMetricsUnavailable)
            quota_guard()
            raw = provider().option_chain(*option_known[body.symbol], body.expiry.isoformat())
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
        except Exception as exc:
            provider_read_error(exc, "Clone Dhan option chain unavailable")
        return JSONResponse({"source": "dhan", "symbol": body.symbol,
                             "expiry": body.expiry.isoformat(), **metrics,
                             "atm_window": window, "atm_window_status": window_status,
                             "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    # ---- B244: server-side PAPER position manager (no orders of any kind) ----
    try:
        from .server_paper_positions import PaperEngine
    except ImportError:
        from server_paper_positions import PaperEngine
    paper = PaperEngine(os.environ.get("BOTKING_PAPER_STATE_FILE"))

    class PaperOpen(BaseModel):
        symbol: str
        side: str
        qty: int
        entry: float
        stop: float
        target: Optional[float] = None

    class PaperClose(BaseModel):
        id: str
        price: Optional[float] = None

    def paper_json(payload):
        payload = dict(payload)
        payload["live_orders_enabled"] = False
        return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    @app.get("/clone-v2/paper/heartbeat")
    def paper_heartbeat(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        return paper_json(paper.heartbeat())

    @app.get("/clone-v2/paper/state")
    def paper_state(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        return paper_json(paper.state())

    @app.post("/clone-v2/paper/open")
    def paper_open(body: PaperOpen, x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if body.symbol not in known:
            raise HTTPException(422, "Unknown symbol")
        try:
            pos = paper.open(body.symbol, body.side, body.qty, body.entry,
                             body.stop, body.target)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        return paper_json({"position": pos})

    @app.post("/clone-v2/paper/close")
    def paper_close(body: PaperClose, x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        try:
            pos = paper.close(body.id, body.price)
        except KeyError:
            raise HTTPException(404, "Open paper position not found") from None
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        return paper_json({"position": pos})

    def read_private_text(env_name, default, limit):
        path = os.environ.get(env_name, default)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read(limit + 1)[:limit]
        except OSError:
            return ""

    @app.get("/clone-v2/signals/latest")
    def signals_latest(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        raw = read_private_text("BOTKING_SIGNALS_FILE",
            "/home/opc/botking-clone-v2-private/signals-latest.json", 65536)
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            data = {"available": False, "reason": "NO_SERVER_SIGNAL_FILE"}
        return paper_json(data)

    @app.get("/clone-v2/signals/journal")
    def signals_journal(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        raw = read_private_text("BOTKING_SIGNALS_JOURNAL",
            "/home/opc/botking-clone-v2-private/signals-journal.jsonl", 65536)
        events = []
        for line in raw.splitlines()[-60:]:
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    events.append(row)
            except ValueError:
                continue
        return paper_json({"events": events})

    def paper_poll_once():
        """Quote only the symbols of OPEN paper positions, inside the shared
        spacing/quota gates. Returns closed positions. Read-only Dhan LTP."""
        symbols = [x for x in paper.heartbeat()["open_symbols"] if x in known]
        if not symbols or not regular_session_now() or quota_remaining() > 0:
            return []
        with market_lock:
            wait = 1.05 - (time.monotonic() - last_request[0])
            if 0 < wait <= 1.05:
                time.sleep(wait)
            last_request[0] = time.monotonic()
            feed = provider()
            reader = getattr(feed, "batch_quote", None)
            result = (reader if callable(reader) else feed.batch_ltp)([known[x] for x in symbols])
        prices = {}
        if isinstance(result, dict) and isinstance(result.get("data"), dict):
            for sym in symbols:
                seg, sid = known[sym]
                try:
                    prices[sym] = float(result["data"][seg][str(sid)]["last_price"])
                except (KeyError, TypeError, ValueError):
                    pass
        return paper.observe(prices)

    def paper_poll_loop():
        while True:
            time.sleep(20)
            try:
                paper_poll_once()
            except Exception as exc:  # keep the engine alive; never raise
                paper.last_error = type(exc).__name__
                try:
                    quota_start() if "429" in str(exc) else None
                except Exception:
                    pass

    if os.environ.get("BOTKING_PAPER_POLL") == "1":
        threading.Thread(target=paper_poll_loop, name="paper-poll", daemon=True).start()
    app.state.paper_engine = paper
    app.state.paper_poll_once = paper_poll_once

    return app
