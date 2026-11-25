"""Local-only CPU worker budget and measured execution; never schedules broker requests."""
import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

def worker_budget(cpus=None, available_bytes=None):
    if cpus is None:
        try:
            cpus=len(os.sched_getaffinity(0))
        except (AttributeError,OSError):
            cpus=os.cpu_count() or 1
    if available_bytes is None:
        try:
            available_bytes=os.sysconf("SC_AVPHYS_PAGES")*os.sysconf("SC_PAGE_SIZE")
        except (AttributeError,OSError,ValueError):
            available_bytes=None
    cores=max(1,int(cpus))
    # Reserve a core for UI/network; unknown memory starts conservatively.
    memory_budget=max(1,int(available_bytes)//(256*1024*1024)) if available_bytes is not None and available_bytes>0 else 2
    return max(1,min(max(1,cores-1),memory_budget,8))

class LocalAnalysisPool:
    def __init__(self,workers=None):
        self.workers=worker_budget() if workers is None else max(1,int(workers))
        self._executor=ThreadPoolExecutor(max_workers=self.workers,thread_name_prefix="bk-local")
        self._lock=Lock()
        self._pending=0
        self._running=0
        self._completed=0
        self._failed=0
        self._cancelled=0
        self._running_cancel_waits=0
        self._queue_last_ms=0.0
        self._queue_max_ms=0.0
        self._compute_last_ms=0.0
        self._compute_max_ms=0.0
        self._thread_cpu_total_seconds=0.0
        self._thread_cpu_samples=0
        self._thread_cpu_last_ms=None
    async def run(self,fn,*args,**kwargs):
        queued=time.perf_counter()
        with self._lock:self._pending+=1
        def execute():
            began=time.perf_counter()
            clock=getattr(time,"thread_time",None)
            cpu_began=clock() if clock is not None else None
            with self._lock:
                self._pending-=1
                self._running+=1
                self._queue_last_ms=round((began-queued)*1000,3)
                self._queue_max_ms=max(self._queue_max_ms,self._queue_last_ms)
            try:
                return fn(*args,**kwargs)
            except Exception:
                with self._lock:self._failed+=1
                raise
            finally:
                cpu_elapsed=max(0.0,clock()-cpu_began) if cpu_began is not None else None
                with self._lock:
                    if cpu_elapsed is not None:
                        self._thread_cpu_samples+=1
                        self._thread_cpu_total_seconds+=cpu_elapsed
                        self._thread_cpu_last_ms=round(cpu_elapsed*1000,3)
                    self._running-=1
                    self._completed+=1
                    self._compute_last_ms=round((time.perf_counter()-began)*1000,3)
                    self._compute_max_ms=max(self._compute_max_ms,self._compute_last_ms)
        try:
            future=self._executor.submit(execute)
        except Exception:
            with self._lock:self._pending-=1
            raise
        def done(f):
            if f.cancelled():
                with self._lock:
                    self._pending-=1
                    self._cancelled+=1
        future.add_done_callback(done)
        wrapped=asyncio.wrap_future(future)
        try:
            return await asyncio.shield(wrapped)
        except asyncio.CancelledError:
            # Queued jobs can be cancelled immediately. A running thread cannot
            # be killed safely; retain the caller's ownership until it exits.
            if not future.cancel():
                with self._lock:self._running_cancel_waits+=1
                while not wrapped.done():
                    try:
                        await asyncio.shield(wrapped)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if wrapped.done() and not wrapped.cancelled():
                    wrapped.exception()  # consume abandoned failure
            raise
    def diagnostics(self):
        # Linux/Android process RSS, not system-wide memory or Python heap.
        rss_bytes=None
        try:
            with open('/proc/self/status',encoding='ascii') as status:
                for line in status:
                    if line.startswith('VmRSS:'):
                        parts=line.split()
                        if len(parts)==3 and parts[2]=='kB':
                            rss_bytes=int(parts[1])*1024
                        break
        except (OSError,ValueError,UnicodeError):
            pass
        with self._lock:
            return {"workers":self.workers,"pending":self._pending,"running":self._running,
                    "completed":self._completed,"failed":self._failed,"cancelled":self._cancelled,
                    "running_cancel_waits":self._running_cancel_waits,
                    "queue_last_ms":self._queue_last_ms,"queue_max_ms":self._queue_max_ms,
                    "compute_last_ms":self._compute_last_ms,"compute_max_ms":self._compute_max_ms,
                    "thread_cpu_samples":self._thread_cpu_samples,
                    "thread_cpu_total_ms":round(self._thread_cpu_total_seconds*1000,3) if self._thread_cpu_samples else None,
                    "thread_cpu_last_ms":self._thread_cpu_last_ms,
                    "process_rss_bytes":rss_bytes,
                    "scope":"local_analysis_only","provider_requests":0}
    def close(self):
        self._executor.shutdown(wait=False,cancel_futures=True)

# One shared pool for the app process, rather than a pool per screen or session.
local_analysis_pool=LocalAnalysisPool()
