"""Bounded, atomic local storage for last successful PUBLIC market snapshots."""
import copy
import json
import math
import os
from pathlib import Path
from threading import RLock
import time

PRIVATE={"apikey","apisecret","accesstoken","refreshtoken","feedtoken","jwttoken",
         "password","mpin","totp","authorization","clientcode","credentials"}
def public_copy(value):
    if isinstance(value,dict):
        return {str(k):public_copy(v) for k,v in value.items()
                if str(k).lower().replace("_","").replace(" ","") not in PRIVATE}
    if isinstance(value,(list,tuple)):return [public_copy(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value):raise ValueError("Nonfinite snapshot")
    if value is None or isinstance(value,(str,int,float,bool)):return value
    raise ValueError("Unsupported snapshot value")

class SnapshotStore:
    def __init__(self,path,max_entries=160):
        self.path=Path(path);self.max_entries=max_entries;self.lock=RLock();self.records={}
        self.status="No saved market snapshots"
        try:
            if self.path.exists():
                if self.path.stat().st_size>24*1024*1024:raise ValueError("Cache too large")
                data=json.loads(self.path.read_text(encoding="utf-8"))
                if data.get("version")!=1 or not isinstance(data.get("records"),dict):raise ValueError("Invalid cache")
                for key,record in data["records"].items():
                    if isinstance(record,dict) and isinstance(record.get("saved_at"),(int,float)) and isinstance(record.get("payload"),dict):
                        self.records[key]=public_copy(record)
                self.records=dict(sorted(self.records.items(),key=lambda p:p[1]["saved_at"])[-max_entries:])
                self.status="Saved market snapshots restored"
        except (OSError,ValueError,TypeError):self.records={};self.status="Saved cache unreadable; fresh data can restore it"
    @staticmethod
    def key(kind,*parts):return json.dumps([kind]+list(parts),ensure_ascii=False,separators=(",",":"))
    @staticmethod
    def valid(kind,p):
        if not isinstance(p,dict):return False
        if kind in ("market","option_chart"):
            bars=p.get("bars")
            if not isinstance(bars,list) or not bars:return False
            for row in bars:
                if not isinstance(row,(list,tuple)) or len(row)<6:return False
                if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in row[:6]):return False
            if kind=="market" and (not isinstance(p.get("price"),(int,float)) or not math.isfinite(p["price"])):return False
        elif kind=="ranking":
            rows=p.get("rows")
            if not isinstance(rows,list) or not rows or len(rows)>5:return False
            if any(not isinstance(r,dict) or not isinstance(r.get("symbol"),str) or r.get("bias") not in ("BULLISH","BEARISH","WAIT","DATA UNAVAILABLE") for r in rows):return False
            if any(r.get("timestamp") is not None and (not isinstance(r["timestamp"],(int,float)) or not math.isfinite(r["timestamp"])) for r in rows):return False
        elif kind=="options":
            rows=p.get("rows")
            if not isinstance(rows,list) or not rows or len(rows)>50:return False
            if any(not isinstance(r,dict) or not all(k in r for k in ("side","strike","premium","timestamp")) or r["side"] not in ("CE","PE") for r in rows):return False
            if any(not isinstance(r.get(k),(int,float)) or not math.isfinite(r[k]) or r[k]<0 for r in rows for k in ("strike","premium")):return False
        elif kind=="analysis":
            if not all(isinstance(p.get(k),str) for k in ("direction","basis","tf","symbol")):return False
        elif kind=="fusion":
            if not all(isinstance(p.get(k),dict) for k in ("candle","options","news")):return False
            if not all(k in p for k in ("overall","coverage","reason","headlines","global_headlines","news_status","global_status")):return False
        elif kind=="news":
            if not isinstance(p.get("items"),list) or not isinstance(p.get("fetched"),(int,float)):return False
            if any(not isinstance(r,dict) or not all(k in r for k in ("title","url","published","source")) for r in p["items"]):return False
        else:return False
        return True
    def get(self,kind,*parts):
        with self.lock:
            item=self.records.get(self.key(kind,*parts))
            return copy.deepcopy(item["payload"]) if item and self.valid(kind,item["payload"]) else None
    def put(self,kind,parts,payload):
        safe=public_copy(payload)
        if not safe:return False
        if not self.valid(kind,safe):return False
        if kind=="market" and (not safe.get("bars") or safe.get("price") is None):return False
        if kind=="ranking" and not safe.get("rows"):return False
        if kind=="options" and not safe.get("rows"):return False
        if kind=="news" and not safe.get("items"):return False
        if "bars" in safe:safe["bars"]=safe["bars"][-600:]
        key=self.key(kind,*parts)
        with self.lock:
            previous=self.records.get(key,{}).get("payload")
            if kind=="market" and previous and self.valid(kind,previous):
                old_time=previous.get("quote_timestamp") or previous["bars"][-1][0]
                new_time=safe.get("quote_timestamp") or safe["bars"][-1][0]
                if new_time<old_time:return False
            records=dict(self.records);records[key]={"saved_at":time.time(),"payload":safe}
            records=dict(sorted(records.items(),key=lambda p:p[1]["saved_at"])[-self.max_entries:])
            temp=self.path.with_name(self.path.name+".tmp")
            try:
                raw=json.dumps({"version":1,"records":records},ensure_ascii=False,allow_nan=False)
                if len(raw.encode("utf-8"))>24*1024*1024:raise ValueError("Cache too large")
                self.path.parent.mkdir(parents=True,exist_ok=True)
                with temp.open("w",encoding="utf-8") as f:
                    f.write(raw);f.flush();os.fsync(f.fileno())
                os.replace(temp,self.path);self.records=records
                self.status="Last successful market data saved"
                return True
            except (OSError,ValueError):
                self.status="Market cache save failed; current data remains on screen"
                try:temp.unlink(missing_ok=True)
                except OSError:pass
                return False
    def latest_markets(self):
        with self.lock:
            result={}
            for key,record in sorted(self.records.items(),key=lambda p:p[1]["saved_at"]):
                try:parts=json.loads(key)
                except ValueError:continue
                if len(parts)==5 and parts[0]=="market" and self.valid("market",record["payload"]):
                    result[parts[2]]=dict(copy.deepcopy(record["payload"]),cached=True)
            return result

def age_label(stamp,now=None):
    if not isinstance(stamp,(int,float)) or not math.isfinite(stamp):return "Time unavailable"
    age=(time.time() if now is None else now)-stamp
    if age<0:return "Invalid future time"
    if age<60:return f"{int(age)} sec old"
    if age<3600:return f"{int(age//60)} min old"
    if age<86400:return f"{int(age//3600)} hours old"
    return f"{int(age//86400)} days old"
