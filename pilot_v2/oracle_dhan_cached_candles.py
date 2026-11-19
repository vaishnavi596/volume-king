"""Read cached Dhan 1m/5m bars from protected Oracle, derive complete 3m only.

The V1 Oracle route /v2/candles/{symbol}/{interval} has no native 3-minute
interval. Three verified consecutive 1m observations can be aggregated to one
*historical* 3m bar only after a conservative close-time delay. Never mark LIVE,
invent missing minutes, or call Dhan directly; no phone-controlled URLs.
"""
import json
import math
import time
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, ProxyHandler, build_opener

from .oracle_evidence_lane import DhanEvidenceBatch
from .internal_dhan_read_port import DhanReadUnavailable

_LOOPBACK = "http://127.0.0.1:8000"
_MAX_RESPONSE = 196608


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, url):
        return None


def _ohlcv(row):
    """A real Dhan cached row is [Unix-second, O, H, L, C, volume]."""
    if type(row) is not list or len(row) != 6:
        raise ValueError("Invalid Dhan historical bar")
    ts, op, hi, lo, cl, vol = row
    if (type(ts) is not int or ts <= 0 or ts % 60 != 0
            or any(type(x) not in (float, int) or not math.isfinite(x)
                   for x in (op, hi, lo, cl, vol))
            or min(op, hi, lo, cl) <= 0 or vol < 0
            or hi < max(op, lo, cl) or lo > min(op, hi, cl)):
        raise ValueError("Invalid OHLCV")
    return (ts, float(op), float(hi), float(lo), float(cl), float(vol))


def normalize_cached_bars(rows, *, timeframe, now):
    """Return only independently complete periods, never partial 3m bars."""
    if (type(rows) is not list or not 2 <= len(rows) <= 5000
            or timeframe not in ("1m", "3m", "5m")
            or type(now) not in (int, float) or not math.isfinite(now) or now <= 0):
        raise ValueError("Unverified cached historical series")
    complete = []
    prev = 0
    for row in rows:
        ts, op, hi, lo, cl, vol = _ohlcv(row)
        if ts <= prev:
            raise ValueError("Unordered Dhan candle history")
        prev = ts
        # V1 cached candle timestamps mark interval start. Always exclude
        # potentially open bars, with an additional minute of safety.
        source_interval = 300 if timeframe == "5m" else 60
        if ts + source_interval + 60 <= now:
            complete.append((ts, op, hi, lo, cl, vol))
    if timeframe == "3m":
        source = {bar[0]: bar for bar in complete}
        candles = []
        for ts in sorted(source):
            if ts % 180:
                continue
            bars = [source.get(ts + i * 60) for i in range(3)]
            if None in bars or ts + 240 > now:
                continue
            candles.append((ts, bars[0][1], max(b[2] for b in bars),
                            min(b[3] for b in bars), bars[-1][4],
                            sum(b[5] for b in bars)))
    else:
        candles = complete
    # Display stays HIST_UNVERIFIED; never fill gaps or fabricate votes.
    if len(candles) < 2:
        raise ValueError("Insufficient completed Dhan history")
    return [
        {"timestamp": ts, "open": op, "high": hi, "low": lo,
         "close": cl, "volume": vol, "completed": True}
        for ts, op, hi, lo, cl, vol in candles[-2000:]
    ]


class OracleDhanCachedCandleTransport:
    """One operator-selected cached Dhan candle read, zero provider fanout."""

    def __init__(self, *, pairing_key, symbol, timeframe="3m", opener=None, clock=None):
        if (type(pairing_key) is not str or len(pairing_key) < 32
                or type(symbol) is not str or not 1 <= len(symbol) <= 32
                or not all(c.isupper() or c.isdigit() or c in "&_-" for c in symbol)
                or timeframe not in ("1m", "3m", "5m")):
            raise ValueError("Approved cached Dhan candle source required")
        self._pairing_key = pairing_key
        self._symbol = symbol
        self._timeframe = timeframe
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())
        self._clock = clock or time.time
        self._lock = Lock()
        self._revision = 0

    def __call__(self):
        interval = "5" if self._timeframe == "5m" else "1"
        url = f"{_LOOPBACK}/v2/candles/{self._symbol}/{interval}"
        request = Request(url, method="GET",
                          headers={"X-BotKing-Key": self._pairing_key,
                                   "Accept": "application/json"})
        try:
            with self._opener.open(request, timeout=10) as response:
                if response.status != 200 or response.geturl() != url:
                    raise DhanReadUnavailable("Oracle candle source unavailable")
                raw = response.read(_MAX_RESPONSE + 1)
                if len(raw) > _MAX_RESPONSE:
                    raise DhanReadUnavailable("Oversized historical candle snapshot")
        except HTTPError:
            raise DhanReadUnavailable("Oracle candle cache unavailable") from None
        except (URLError, TimeoutError, OSError):
            raise DhanReadUnavailable("Oracle candle cache unavailable") from None
        try:
            payload = json.loads(raw)
            if (type(payload) is not dict or payload.get("source") != "dhan"
                    or payload.get("symbol") != self._symbol
                    or payload.get("interval") != interval + "m"
                    or payload.get("freshness") != "historical_unverified"
                    or payload.get("live_orders_enabled") is not False):
                raise ValueError("Historical Dhan provenance unavailable")
            now = self._clock()
            bars = normalize_cached_bars(payload.get("bars"),
                                         timeframe=self._timeframe, now=now)
        except (TypeError, ValueError, OverflowError):
            raise DhanReadUnavailable("Incomplete Dhan cached history") from None
        with self._lock:
            self._revision += 1
            revision = self._revision
        return DhanEvidenceBatch("dhan", revision, now, [{
            "kind": "candles", "symbol": self._symbol,
            "timeframe": self._timeframe, "revision": revision,
            "bars": bars}])
