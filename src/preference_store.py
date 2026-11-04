"""Serialize preference writes without blocking Flet's event loop on native RPC."""
import asyncio
import copy
import json
import os
from pathlib import Path
from threading import RLock

def load_preferences(path,storage):
    disk={};native={}
    try:
        disk=json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(disk,dict):disk={}
    except (OSError,ValueError,TypeError):pass
    try:
        native=storage.get("bot_king_preferences")
        if not isinstance(native,dict):native={}
    except Exception:pass
    def revision(value):
        try:return max(0,int(value.get("_prefs_revision",0)))
        except (ValueError,TypeError,OverflowError):return 0
    result=dict(disk if revision(disk)>revision(native) else native or disk)
    result["_prefs_revision"]=revision(result)
    return result

class PreferenceWriter:
    def __init__(self,page,path,revision=0,on_error=None):
        self.page=page;self.path=Path(path);self.revision=revision
        self.on_error=on_error or (lambda exc:None)
        self.lock=RLock();self.pending=None;self.running=False
        self.status="Ready";self.disk_saved=False
    def save(self,values):
        schedule=False
        with self.lock:
            self.revision+=1
            snapshot=copy.deepcopy(values)
            snapshot["_prefs_revision"]=self.revision
            self.disk_saved=False
            temp=self.path.with_name(self.path.name+".tmp")
            try:
                self.path.parent.mkdir(parents=True,exist_ok=True)
                raw=json.dumps(snapshot,ensure_ascii=False,allow_nan=False)
                with temp.open("w",encoding="utf-8") as output:
                    output.write(raw);output.flush();os.fsync(output.fileno())
                os.replace(temp,self.path);self.disk_saved=True
            except (OSError,ValueError,TypeError) as exc:
                self.on_error(exc)
                try:temp.unlink(missing_ok=True)
                except OSError:pass
            if hasattr(self.page.client_storage,"set_async"):
                self.pending=snapshot;self.status="Saving native preferences..."
                if not self.running:self.running=True;schedule=True
            else:
                # Compatibility for synchronous test adapters, not the Android bridge.
                try:
                    result=self.page.client_storage.set("bot_king_preferences",snapshot)
                    if result is False:raise OSError("Native preference write rejected")
                    self.status="Preferences saved";return True
                except Exception as exc:
                    self.on_error(exc)
                    self.status="Local preferences saved" if self.disk_saved else "Preference save failed"
                    return self.disk_saved
        if schedule:
            try:self.page.run_task(self.flush)
            except Exception as exc:
                with self.lock:self.running=False
                self.on_error(exc);self.status="Local preferences saved" if self.disk_saved else "Preference save failed"
        return self.disk_saved
    async def flush(self):
        while True:
            with self.lock:
                snapshot=self.pending;self.pending=None
                if snapshot is None:self.running=False;return
            try:
                result=await self.page.client_storage.set_async("bot_king_preferences",snapshot)
                if result is False:raise OSError("Native preference write rejected")
                self.status="Preferences saved"
            except Exception as exc:
                self.on_error(exc)
                self.status="Local preferences saved" if self.disk_saved else "Preference save failed"
