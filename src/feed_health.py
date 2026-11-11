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
        ):
            if detail.startswith(message + " (HTTP "):
                return message
        if "HTTP 429" in detail or "rate limited" in detail or "cooldown" in detail:
            return "Dhan market data rate limited (HTTP 429); wait before retrying"
        if detail.startswith("Dhan has no candles for requested dates "):
            return "Dhan historical candles unavailable for requested dates"
        if detail == "Dhan returned no verified candles":
            return "Dhan returned no usable historical candles"
        if detail.startswith("Dhan history failed in first pass"):
            return "Dhan historical scan failed; no duplicate request made"
        if "Invalid Dhan candle response" in detail:
            return "Dhan historical response invalid"
        if "Dhan candle timestamp is in the future" in detail:
            return "Dhan candle timestamp invalid"
        if "Dhan candle instrument or interval not verified" in detail:
            return "Dhan instrument or candle interval unsupported"
        if "Invalid Dhan quote" in detail:return "Dhan quote response missing or invalid"
        if "Invalid Dhan status" in detail:return "Dhan status response missing or invalid"
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
