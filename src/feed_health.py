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
    if type(exc).__name__=="ServerBusy":return "Server busy after safe read retries; try again shortly"
    if type(exc).__name__=="FeedError":
        # Only fixed adapter messages; never render arbitrary upstream text.
        message=str(exc)
        known={"Broker feed not connected":"Broker disconnected; connect in Settings",
               "Broker candles unavailable":"Broker returned no candles for this selection",
               "Broker quote unavailable":"Broker returned no quote for this symbol",
               "Broker quote timestamp unavailable or invalid":"Broker quote time missing/invalid; cannot label data live",
               "Listed expiry unavailable":"No listed expiry found for this symbol",
               "Server connection failed; verify HTTPS and network":"Server connection failed; check HTTPS/network",
               "Server rejected request; check server access and broker login":"Server rejected data request; check session/API access",
               "Broker rejected request; reconnect or verify contract":"Broker rejected request; verify API access/contract"}
        if message in known:return known[message]
    return "Data request failed ("+type(exc).__name__+")"

def retry_delay(failures):
    return min(300,30*2**min(max(int(failures)-1,0),4))
