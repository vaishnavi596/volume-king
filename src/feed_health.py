"""Per-component request status; stores no credentials or server response bodies."""
import copy
import time
from threading import RLock

class FeedHealth:
    def __init__(self,clock=time.time):
        self.clock=clock;self.rows={};self.lock=RLock();self.serial=0
    def begin(self,key):
        with self.lock:
            self.serial+=1
            row=self.rows.setdefault(key,{})
            row.update(request_id=self.serial,last_attempt=self.clock(),state="LOADING")
            return self.serial
    def finish(self,key,request_id,state,source="",data_time=None,error=""):
        with self.lock:
            row=self.rows.get(key,{})
            if row.get("request_id")!=request_id:return False
            row.update(state=state,source=source,data_time=data_time,error=error)
            if state in ("AVAILABLE","FALLBACK","PARTIAL","HISTORICAL"):
                row["last_success"]=self.clock()
            return True
    def get(self,key):
        with self.lock:return copy.deepcopy(self.rows.get(key,{}))

def safe_error(exc):
    # Never display raw exception text, URLs, API headers, PIN or token values.
    from urllib.error import HTTPError
    if isinstance(exc,HTTPError):
        if exc.code in (401,403):return "Provider access denied (HTTP "+str(exc.code)+"); check source permissions"
        if exc.code==429:return "Provider request limit; retry later"
        return "Provider HTTP error "+str(exc.code)
    if isinstance(exc,TimeoutError):return "Network timeout"
    if type(exc).__name__=="SessionExpired":return "Broker session expired; reconnect"
    if type(exc).__name__=="FeedError":
        # Match only known adapter phrases; never echo raw URLs or credentials.
        detail=str(exc)
        if "HTTP 403" in detail:return "Dhan server access rejected (HTTP 403); reconnect"
        # Only these adapter-generated, allowlisted messages may be displayed.
        for message in (
            "Dhan token expired or market-data permission missing",
            "Dhan batch rejected; check entitlement and instrument mapping",
            "Dhan batch response invalid or too large",
            "Dhan batch network request failed",
            "Dhan server credentials not configured",
            "Dhan batch returned no NSE equity quotes",
            "Dhan batch response invalid",
            "Dhan historical endpoint unavailable or token expired",
            "Dhan historical candle response invalid",
        ):
            if detail.startswith(message + " (HTTP "):
                return message
        if detail.startswith("/dhan/") and " HTTP 429; retry after " in detail:
            return "Dhan API rate limited (HTTP 429); wait before retry"
        if detail.startswith("/dhan/") and " cooldown: retry in " in detail:
            return "Dhan API cooldown active; wait before retry"
        # Only exact, locally generated Clone adapter messages; never echo
        # raw upstream response, URL, access key, or arbitrary provider text.
        clone_diagnostics = {
            "Clone Dhan candles unavailable": "Clone candle gateway unavailable; check Oracle/Dhan route",
            "Clone market candles HTTP 424": "Dhan authorization required for Clone candles",
            "Clone market candles HTTP 429": "Clone candle provider cooldown; retry later",
            "Clone market candles HTTP 422": "Clone candle symbol, interval or date rejected (HTTP 422)",
            "Clone market candles HTTP 502": "Clone candle upstream unavailable (HTTP 502)",
            "Clone market candles HTTP 503": "Clone candle upstream unavailable (HTTP 503)",
            "Verified Clone Dhan symbol unavailable": "Clone quote route returned no verified quote for requested index; check Dhan index response",
            "Clone market no validated quotes": "Clone index quote response incomplete or no validated price; inspect SENSEX BSE_I/51 provider segment",
            "Clone market data unavailable": "Clone index quote gateway network/response unavailable",

            "Clone candle response not verified": "Clone returned invalid candle data contract",
            "Clone unsupported candle interval": "Clone candle timeframe unsupported",
            "Clone listed option expiries invalid": "Clone option expiry response invalid",
            "Clone option evidence unavailable": "Clone option-chain metrics unavailable",
            "Clone Dhan options/expiries unavailable": "Clone option expiry gateway unavailable",
            "Clone Dhan options/chain unavailable": "Clone option-chain gateway unavailable",
        }
        if detail in clone_diagnostics:
            return clone_diagnostics[detail]
        if "HTTP 422" in detail:
            return "Dhan request rejected (HTTP 422); verify symbol and date range"
        if "Dhan candle instrument or interval not verified" in detail:
            return "Dhan candle mapping or timeframe unsupported"
        if "Invalid Dhan candle response" in detail:
            return "Dhan candle response missing or invalid"
        if detail.startswith("Oracle Dhan snapshot missing, stale or invalid"):
            return "Oracle snapshot stale or invalid; last Dhan prices retained, check server collection"
        if detail.startswith("Oracle Dhan snapshot contains no quotes"):
            return "Oracle snapshot has no equity quotes; check server collection"
        if detail.startswith("Invalid Oracle Dhan snapshot quote"):
            return "Oracle snapshot contains invalid equity price; check server instrument data"
        if detail.startswith("Server Access Key contains non-ASCII"):
            return "Server Access Key contains invalid characters; re-enter plain ASCII key"
        if "Dhan server not connected" in detail:
            return "Dhan server disconnected; reconnect in Settings"
        if "Unexpected Dhan read-only server response" in detail:
            return "Dhan server response failed read-only validation"
        if any("HTTP "+str(code) in detail for code in (502,503,504)):
            return "Dhan upstream temporarily unavailable; retry later"
        if "HTTPS connection or response failed" in detail:
            return "Dhan HTTPS connection failed or timed out; retry"
        if "response too large" in detail:return "Dhan response exceeded safety limit"
        if "Invalid Dhan batch" in detail or "Empty Dhan batch" in detail:
            return "Dhan batch response missing or invalid"
    return "Data request failed ("+type(exc).__name__+")"

def retry_delay(failures):
    return min(300,30*2**min(max(int(failures)-1,0),4))
