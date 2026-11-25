"""Bounded, atomic local storage for last successful PUBLIC market snapshots."""
import copy
import json
import math
import os
try:
    import sqlite3
except ImportError:
    sqlite3=None
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

MAX_CACHE_BYTES=64*1024*1024
MAX_CACHE_BARS=1200

class SnapshotStore:
    def __init__(self,path,max_entries=1200,*,incremental=False):
        self.path=Path(path);self.max_entries=max_entries;self.lock=RLock();self.records={}
        self.status="No saved market snapshots"
        self.evicted=0;self.rejected=0;self.restored=0;self.save_failures=0
        self.file_bytes=0
        self.write_count=0;self.write_last_ms=0.0;self.write_max_ms=0.0
        self.unchanged_writes_skipped=0
        self.incremental=bool(incremental and sqlite3 is not None)
        self.fallback_reason="sqlite_unavailable" if incremental and sqlite3 is None else None
        self.db_path=self.path.with_name(self.path.name+".sqlite3")
        self._record_sizes={}
        if self.incremental:
            self._restore_incremental()
            if not self.save_failures:return
            self.incremental=False
            self.fallback_reason="sqlite_restore_failed"
            # Do not overwrite the original migration backup after a failed DB restore.
            self.path=self.path.with_name(self.path.name+".recovery.json")
        try:
            if self.path.exists():
                if self.path.stat().st_size>MAX_CACHE_BYTES:raise ValueError("Cache too large")
                data=json.loads(self.path.read_text(encoding="utf-8"))
                if data.get("version")!=1 or not isinstance(data.get("records"),dict):raise ValueError("Invalid cache")
                for key,record in data["records"].items():
                    if isinstance(record,dict) and isinstance(record.get("saved_at"),(int,float)) and isinstance(record.get("payload"),dict):
                        self.records[key]=public_copy(record)
                self.records=dict(sorted(self.records.items(),key=lambda p:p[1]["saved_at"])[-max_entries:])
                self.restored=len(self.records);self.file_bytes=self.path.stat().st_size
                self.status="Saved market snapshots restored"
        except (OSError,ValueError,TypeError):self.records={};self.status="Saved cache unreadable; fresh data can restore it"
    def _connect_incremental(self):
        self.db_path.parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(str(self.db_path),timeout=5)
        try:
            db.execute("CREATE TABLE IF NOT EXISTS snapshots (key TEXT PRIMARY KEY, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.commit()
            return db
        except Exception:
            db.close()
            raise
    @staticmethod
    def _encode_record(record):
        return json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(",",":"))
    def _restore_incremental(self):
        db=None
        try:
            db=self._connect_incremental()
            initialized=db.execute("SELECT value FROM metadata WHERE key='initialized'").fetchone()
            if not initialized:
                # Preserve the original JSON file as rollback material.
                legacy=SnapshotStore(self.path,self.max_entries)
                if self.path.exists() and legacy.status!="Saved market snapshots restored":
                    raise ValueError("Legacy cache unreadable")
                with db:
                    db.executemany("INSERT OR REPLACE INTO snapshots VALUES (?,?)",
                        [(k,self._encode_record(v)) for k,v in legacy.records.items()])
                    db.execute("INSERT INTO metadata VALUES ('initialized','1')")
            rows={}
            for key,raw in db.execute("SELECT key,record FROM snapshots"):
                try:
                    record=public_copy(json.loads(raw))
                    parts=json.loads(key)
                except (ValueError,TypeError):
                    self.rejected+=1
                    continue
                if (isinstance(parts,list) and parts and isinstance(record,dict)
                        and type(record.get("saved_at")) in (int,float)
                        and math.isfinite(record["saved_at"])
                        and self.valid(parts[0],record.get("payload"))
                        and self.identity_valid(parts[0],parts[1:],record["payload"])):
                    rows[key]=record
            self.records=dict(sorted(rows.items(),key=lambda p:p[1]["saved_at"])[-self.max_entries:])
            with db:
                db.executemany("DELETE FROM snapshots WHERE key=?",[(k,) for (k,) in db.execute("SELECT key FROM snapshots").fetchall() if k not in self.records])
            self._record_sizes={k:len(k.encode("utf-8"))+len(self._encode_record(v).encode("utf-8")) for k,v in self.records.items()}
            self.file_bytes=sum(self._record_sizes.values())
            self.restored=len(self.records)
            self.status="Incremental market snapshots restored"
        except (OSError,ValueError,TypeError,sqlite3.Error):
            self.records={};self._record_sizes={}
            self.status="Incremental cache unreadable; original JSON preserved"
            self.save_failures+=1
        finally:
            if db is not None:db.close()
    def _save_incremental(self,key,record,records):
        started=time.perf_counter()
        db=None
        try:
            raw=self._encode_record(record)
            sizes={k:v for k,v in self._record_sizes.items() if k in records}
            sizes[key]=len(key.encode("utf-8"))+len(raw.encode("utf-8"))
            size=sum(sizes.values())
            if size>MAX_CACHE_BYTES:raise ValueError("Cache too large")
            db=self._connect_incremental()
            if not db.execute("SELECT value FROM metadata WHERE key='initialized'").fetchone():
                raise ValueError("Incremental migration incomplete")
            with db:
                db.execute("INSERT OR REPLACE INTO snapshots VALUES (?,?)",(key,raw))
                db.executemany("DELETE FROM snapshots WHERE key=?",[(k,) for k in self.records if k not in records])
            self.evicted+=len(set(self.records)-set(records))
            self.records=records;self._record_sizes=sizes;self.file_bytes=size
            self.write_count+=1
            self.write_last_ms=round((time.perf_counter()-started)*1000,3)
            self.write_max_ms=max(self.write_max_ms,self.write_last_ms)
            self.status="Last successful market data saved"
            return True
        except (OSError,ValueError,sqlite3.Error):
            self.save_failures+=1
            self.status="Incremental cache save failed; current data remains on screen"
            return False
        finally:
            if db is not None:db.close()
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
            if kind=="market":
                price=p.get("price")
                hist_only=(price is None and p.get("source")=="Dhan"
                           and p.get("live_verified") is False
                           and p.get("freshness")=="historical_unverified"
                           and p.get("_scanner_timeframe") in ("1m","2m","3m","5m",
                                                                 "10m","15m","30m","1h"))
                if hist_only:
                    # A historical-only record must have a nontrivial,
                    # correctly ordered, physically valid Dhan OHLCV series.
                    if len(bars)<30 or any(
                        type(row[0]) not in (int,float) or row[0]<=0
                        or any(type(v) not in (int,float) for v in row[:6])
                        or min(row[1],row[2],row[3],row[4])<=0
                        or row[5]<0 or row[2]<max(row[1],row[4])
                        or row[3]>min(row[1],row[4])
                        for row in bars
                    ) or any(bars[i][0]<=bars[i-1][0] for i in range(1,len(bars))):
                        return False
                if not hist_only and (type(price) not in (int,float)
                                       or not math.isfinite(price) or price<=0):
                    return False
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
        elif kind=="analysis_last_good":
            if (p.get("source")!="Dhan" or p.get("historical") is not True
                    or p.get("live_verified") is not False or p.get("freshness")!="historical_unverified"
                    or not isinstance(p.get("symbol"),str) or not p["symbol"]
                    or p.get("timeframe") not in ("1m","2m","3m","5m","10m","15m","30m","1h")
                    or type(p.get("timestamp")) not in (int,float) or not math.isfinite(p["timestamp"])
                    or p["timestamp"]<=0 or type(p.get("count")) is not int or p["count"]<30
                    or not isinstance(p.get("votes"),list)):return False
        elif kind=="option_context_last_good":
            if (p.get("source")!="dhan" or p.get("signal_eligible") is not False
                    or p.get("live_verified") is True or not isinstance(p.get("symbol"),str)
                    or not p["symbol"] or not isinstance(p.get("expiry"),str)):return False
            from datetime import date
            try:
                if date.fromisoformat(p["expiry"]).isoformat()!=p["expiry"]:return False
            except ValueError:return False
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
    @staticmethod
    def identity_valid(kind,parts,p):
        if kind=="analysis_last_good":return tuple(parts)==("Dhan",p.get("symbol"),p.get("timeframe"))
        if kind=="option_context_last_good":return tuple(parts)==("Dhan",p.get("symbol"),p.get("expiry"))
        return True
    def _physical_bytes(self):
        paths=(self.db_path,Path(str(self.db_path)+"-wal"),Path(str(self.db_path)+"-shm"),Path(str(self.db_path)+"-journal")) if self.incremental else (self.path,)
        total=0
        for path in paths:
            try:total+=path.stat().st_size
            except OSError:pass
        return total
    def diagnostics(self):
        with self.lock:
            counts={}
            for key in self.records:
                try:kind=json.loads(key)[0]
                except (ValueError,IndexError,TypeError):continue
                counts[kind]=counts.get(kind,0)+1
            return {"entries":len(self.records),"max_entries":self.max_entries,
                    "max_bars_per_record":MAX_CACHE_BARS,"file_bytes":self.file_bytes,
                    "max_file_bytes":MAX_CACHE_BYTES,"restored_entries":self.restored,
                    "evicted_since_start":self.evicted,"rejected_since_start":self.rejected,
                    "save_failures_since_start":self.save_failures,"by_kind":counts,
                    "entry_utilization_pct":round(100*len(self.records)/max(1,self.max_entries),2),
                    "byte_utilization_pct":round(100*self.file_bytes/MAX_CACHE_BYTES,2),
                    "capacity_warning":len(self.records)>=0.8*self.max_entries or self.file_bytes>=0.8*MAX_CACHE_BYTES,
                    "write_count":self.write_count,"write_last_ms":self.write_last_ms,
                    "write_max_ms":self.write_max_ms,"unchanged_writes_skipped":self.unchanged_writes_skipped,
                    "storage_backend":"sqlite_incremental" if self.incremental else "json_atomic",
                    "physical_storage_bytes":self._physical_bytes(),"fallback_reason":self.fallback_reason,
                    "byte_metric":"logical_record_bytes" if self.incremental else "file_bytes",
                    "status":self.status,"restored_cache_live_proof":False}
    def get(self,kind,*parts):
        with self.lock:
            item=self.records.get(self.key(kind,*parts))
            return copy.deepcopy(item["payload"]) if item and self.valid(kind,item["payload"]) and self.identity_valid(kind,parts,item["payload"]) else None
    def put(self,kind,parts,payload):
        safe=public_copy(payload)
        if not safe:return False
        if not self.valid(kind,safe) or not self.identity_valid(kind,parts,safe):
            with self.lock:self.rejected+=1
            return False
        # Fully checked history-only Dhan payloads may be persisted without
        # an LTP; SnapshotStore.valid verifies their exact-frame HIST identity.
        if kind=="market" and not safe.get("bars"):return False
        if kind=="ranking" and not safe.get("rows"):return False
        if kind=="options" and not safe.get("rows"):return False
        if kind=="news" and not safe.get("items"):return False
        if "bars" in safe:safe["bars"]=safe["bars"][-MAX_CACHE_BARS:]
        key=self.key(kind,*parts)
        with self.lock:
            previous=self.records.get(key,{}).get("payload")
            if kind=="market" and previous and self.valid(kind,previous):
                # Exchange trade and completed candle clocks are independent.
                if previous["bars"][-1][0]>safe["bars"][-1][0]:
                    safe["bars"]=previous["bars"]
                    for field in ("candle_fetched_at","candle_transport_integrity",
                                  "candle_raw_provider_provenance","candle_transport_digest_scope"):
                        safe.pop(field,None)
                        if field in previous:safe[field]=previous[field]
                old_ts=previous.get("quote_timestamp")
                new_ts=safe.get("quote_timestamp")
                old_valid=type(old_ts) in (int,float) and math.isfinite(old_ts) and old_ts>0
                new_valid=type(new_ts) in (int,float) and math.isfinite(new_ts) and new_ts>0
                if old_valid and (not new_valid or new_ts<old_ts):
                    # An older quote cannot replace a last-good quote even if
                    # a newer candle arrived in the same response.
                    if safe["bars"]==previous["bars"]:return False
                    for field in ("price","quote_timestamp","change","fetched_at"):
                        safe.pop(field,None)
                        if field in previous:safe[field]=previous[field]
                    safe.update(live_verified=False,freshness="unverified")
            if kind=="analysis_last_good" and previous and self.valid(kind,previous) and safe["timestamp"]<previous["timestamp"]:
                self.rejected+=1;return False
            if previous==safe:
                self.unchanged_writes_skipped+=1
                return True
            records=dict(self.records);records[key]={"saved_at":time.time(),"payload":safe}
            if len(records)>self.max_entries:
                records=dict(sorted(records.items(),key=lambda p:p[1]["saved_at"])[-self.max_entries:])
            if self.incremental:
                return self._save_incremental(key,records[key],records)
            temp=self.path.with_name(self.path.name+".tmp")
            started=time.perf_counter()
            try:
                raw=json.dumps({"version":1,"records":records},ensure_ascii=False,allow_nan=False)
                size=len(raw.encode("utf-8"))
                if size>MAX_CACHE_BYTES:raise ValueError("Cache too large")
                self.path.parent.mkdir(parents=True,exist_ok=True)
                with temp.open("w",encoding="utf-8") as f:
                    f.write(raw);f.flush();os.fsync(f.fileno())
                os.replace(temp,self.path)
                self.evicted+=len(set(self.records)-set(records));self.records=records;self.file_bytes=size
                self.write_count+=1
                self.write_last_ms=round((time.perf_counter()-started)*1000,3)
                self.write_max_ms=max(self.write_max_ms,self.write_last_ms)
                self.status="Last successful market data saved"
                return True
            except (OSError,ValueError):
                self.save_failures+=1
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
                if (len(parts)==5 and parts[0]=="market"
                        and self.valid("market",record["payload"])
                        and type(record["payload"].get("price")) in (int,float)):
                    # HIST-only candles are not a last-good LTP quote.
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
