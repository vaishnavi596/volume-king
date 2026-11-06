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
            if state in ("AVAILABLE","FALLBACK","STALE","PARTIAL"):
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
        # Only approved static broker adapter messages may reach the UI.
        # Never show arbitrary server responses or raw transport exceptions.
        allowed=(
            "Broker not connected","Broker feed not connected",
            "Broker request failed; check connection/session",
            "Broker HTTP request failed; retry later",
            "Broker rejected request; reconnect or verify contract",
            "Exact broker symbol unavailable",
            "Broker candles unavailable","Broker quote unavailable",
            "Broker quote is stale; fallback required",
            "Broker session expired; reconnect",
            "Instrument list unavailable","No option quotes returned",
            "No listed contracts for selected expiry; choose a broker-listed date",
        )
        if str(exc) in allowed:return str(exc)
    return "Data request failed ("+type(exc).__name__+")"

def retry_delay(failures):
    return min(300,30*2**min(max(int(failures)-1,0),4))
