"""Append-only, idempotent Brain memory (SQLite). No tokens, no secrets, no orders."""
import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS prediction_event(id TEXT PRIMARY KEY, symbol TEXT, made_at REAL,
  horizon_min INTEGER, call TEXT, p_up REAL, policy_version TEXT, evidence TEXT);
CREATE TABLE IF NOT EXISTS outcome_event(id TEXT PRIMARY KEY, prediction_id TEXT, resolved_at REAL,
  actual_ret REAL, hit INTEGER);
CREATE TABLE IF NOT EXISTS model_policy_version(version TEXT PRIMARY KEY, created_at REAL, note TEXT);
CREATE TRIGGER IF NOT EXISTS no_update_pred BEFORE UPDATE ON prediction_event BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_pred BEFORE DELETE ON prediction_event BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_update_out BEFORE UPDATE ON outcome_event BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_out BEFORE DELETE ON outcome_event BEGIN SELECT RAISE(ABORT,'append-only'); END;
"""


class BrainMemory:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    def add_prediction(self, event_id, symbol, made_at, horizon_min, call, p_up, policy_version, evidence):
        cur = self.db.execute("INSERT OR IGNORE INTO prediction_event VALUES(?,?,?,?,?,?,?,?)",
                              (event_id, symbol, made_at, horizon_min, call, p_up, policy_version,
                               json.dumps(evidence, sort_keys=True)))
        self.db.commit()
        return cur.rowcount == 1          # False when the same id was already stored

    def add_outcome(self, event_id, prediction_id, resolved_at, actual_ret, hit):
        cur = self.db.execute("INSERT OR IGNORE INTO outcome_event VALUES(?,?,?,?,?)",
                              (event_id, prediction_id, resolved_at, actual_ret, int(bool(hit))))
        self.db.commit()
        return cur.rowcount == 1

    def own_record(self, symbol, since_ts):
        row = self.db.execute(
            "SELECT COUNT(*), SUM(o.hit) FROM prediction_event p JOIN outcome_event o ON o.prediction_id=p.id "
            "WHERE p.symbol=? AND p.made_at>=? AND p.call!='WAIT'", (symbol, since_ts)).fetchone()
        n, hits = row[0] or 0, row[1] or 0
        return {"n": n, "hit_rate": (hits / n) if n else None}
