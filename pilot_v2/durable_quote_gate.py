"""Single-host V2 shared quote budget, persistent SQLite lease prototype.

NO BROKER/HTTP CALLS. Production requires approved local filesystem, secure DB
ownership, endpoint-specific throttling, provider auth and rollback testing.
"""
import secrets
import sqlite3
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from .gateway_contract import Demand, ContractError

@dataclass(frozen=True)
class DurableLease:
    token: str
    symbols: tuple

class DurableQuoteGate:
    def __init__(self, path, *, clock, global_spacing=1, symbol_spacing=60, lease_ttl=30):
        if not isinstance(path,(str,Path)) or not str(path) or not callable(clock):
            raise ValueError("Invalid quote store or clock")
        if any(type(v) not in (int,float) or not isfinite(v)
               for v in (global_spacing,symbol_spacing,lease_ttl)):
            raise ValueError("Nonfinite timing")
        if global_spacing<1 or symbol_spacing<30 or not 5<=lease_ttl<=300:
            raise ValueError("Unsafe quote budget")
        self.path=str(path); self.clock=clock
        self.gap=float(global_spacing);self.interval=float(symbol_spacing)
        self.ttl=float(lease_ttl)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS budget(
                id INTEGER PRIMARY KEY CHECK(id=1), last REAL,
                cooldown REAL NOT NULL DEFAULT 0, lease TEXT,
                expires REAL NOT NULL DEFAULT 0)""")
            db.execute("INSERT OR IGNORE INTO budget(id) VALUES(1)")
            db.execute("""CREATE TABLE IF NOT EXISTS attempts(
                symbol TEXT PRIMARY KEY, at REAL NOT NULL)""")

    def _db(self):
        db=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _now(self):
        v=self.clock()
        if type(v) not in (int,float) or not isfinite(v) or v<0:
            raise ContractError("Invalid shared quote clock")
        return float(v)

    def begin(self,demand):
        if not isinstance(demand,Demand):
            raise ContractError("Invalid quote demand")
        syms=tuple(sorted(set(demand.equities+demand.indices)))
        if (len(demand.equities)>70 or len(syms)>73
                or len(set(demand.equities))!=len(demand.equities)
                or len(set(demand.indices))!=len(demand.indices)):
            raise ContractError("Invalid quote budget")
        now=self._now()
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                last,cooldown,lease,expires=db.execute(
                    "SELECT last,cooldown,lease,expires FROM budget WHERE id=1").fetchone()
                if ((last is not None and now<last) or now<cooldown
                        or (lease is not None and now<expires)
                        or (last is not None and now-last<self.gap)):
                    db.execute("COMMIT");return None
                due=[]
                for s in syms:
                    row=db.execute("SELECT at FROM attempts WHERE symbol=?",(s,)).fetchone()
                    if row is None or now-row[0]>=self.interval:
                        due.append(s)
                if not due:
                    db.execute("COMMIT");return None
                token=secrets.token_urlsafe(32)
                db.execute("UPDATE budget SET last=?,lease=?,expires=? WHERE id=1",
                           (now,token,now+self.ttl))
                db.executemany("""INSERT INTO attempts(symbol,at) VALUES(?,?)
                    ON CONFLICT(symbol) DO UPDATE SET at=excluded.at""",
                    [(s,now) for s in due])
                db.execute("COMMIT")
                return DurableLease(token,tuple(due))
            except BaseException:
                db.execute("ROLLBACK");raise

    def complete(self,lease,*,retry_after=None):
        if not isinstance(lease,DurableLease) or type(lease.token) is not str:
            raise ContractError("Invalid quote lease")
        if retry_after is not None and (type(retry_after) not in (int,float)
                or not isfinite(retry_after) or not 1<=retry_after<=3600):
            raise ContractError("Invalid 429 retry-after")
        now=self._now()
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                token,expires,cooldown=db.execute(
                    "SELECT lease,expires,cooldown FROM budget WHERE id=1").fetchone()
                if token!=lease.token or now>=expires:
                    raise ContractError("Stale or expired quote lease")
                delay=max(cooldown,now+retry_after) if retry_after is not None else cooldown
                db.execute("UPDATE budget SET lease=NULL,expires=0,cooldown=? WHERE id=1",
                           (delay,))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK");raise

    def state(self):
        now=self._now()
        with self._db() as db:
            last,cooldown,lease,expires=db.execute(
                "SELECT last,cooldown,lease,expires FROM budget WHERE id=1").fetchone()
        return {"pending":lease is not None and now<expires,
                "cooldown_seconds":max(0.,cooldown-now),"last_global_attempt":last}
