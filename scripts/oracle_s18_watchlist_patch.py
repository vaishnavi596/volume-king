"""S18-B narrow Oracle WatchlistStore patch STAGING ONLY; no service restart.

A security can appear in exactly one of five lists, 70 distinct securities total.
Saved JSON is not changed and pre-existing conflicts are left intact for review.
"""
import argparse
import ast
import hashlib
import os
from pathlib import Path
import shutil
from datetime import datetime, timezone

CHECK = '''        # S18-B: reject a second owner across all five lists.
        other_symbols = set()
        for other_id, other_group in self.data.items():
            if other_id != list_id:
                other_symbols.update(other_group)
        duplicated = set(validated).intersection(other_symbols)
        if duplicated:
            raise WatchlistError("Symbol already belongs to another watchlist")
        previous_total = len(set().union(*(set(group) for group in self.data.values())))
        proposed_total = len(other_symbols.union(validated))
        # Preserve historical over-limit data, but allow only strict reductions.
        if proposed_total > 70 and proposed_total >= previous_total:
            raise WatchlistError("Global limit: 70 symbols across all watchlists")
'''

def make_stage(source):
    tree=ast.parse(source)
    matches=[n for n in ast.walk(tree)
             if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
             and n.name=="replace"
             and [a.arg for a in n.args.args]==["self","list_id","symbols"]]
    if len(matches)!=1:
        raise ValueError("Expected one WatchlistStore.replace")
    method=ast.get_source_segment(source,matches[0]) or ""
    if ("self.data[list_id] = validated" not in method
            or "self.save()" not in method
            or method.count("        previous = self.data[list_id]")!=1
            or "validated = self.validate(symbols)" not in method):
        raise ValueError("Unexpected Oracle WatchlistStore layout")
    if "Symbol already belongs to another watchlist" in source:
        raise ValueError("Global duplicate guard already installed")
    modified=source.replace("        previous = self.data[list_id]",
                            CHECK+"        previous = self.data[list_id]",1)
    ast.parse(modified)
    compile(modified,"watchlist_store.s18.proposed.py","exec")
    return modified

def stage_file(source_path, staging_dir):
    source_path=Path(source_path)
    staging_dir=Path(staging_dir)
    if not source_path.is_file():
        raise ValueError("Oracle watchlist_store.py missing")
    source=source_path.read_text(encoding="utf-8")
    modified=make_stage(source)
    staging_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup=staging_dir/("watchlist_store.s18.before."+stamp+".py")
    proposed=staging_dir/("watchlist_store.s18.proposed."+stamp+".py")
    if backup.exists() or proposed.exists():
        raise ValueError("Staging artifact collision")
    shutil.copy2(source_path,backup)
    proposed.write_text(modified,encoding="utf-8")
    os.chmod(proposed,0o600)
    print("S18_STAGE_SUCCESS: YES")
    print("PRODUCTION_CHANGED: NO")
    print("WATCHLIST_SAVED_JSON_CHANGED: NO")
    print("BACKUP:",backup)
    print("PROPOSED:",proposed)
    print("ORIGINAL_SHA256:",hashlib.sha256(source.encode()).hexdigest())
    print("STAGED_SHA256:",hashlib.sha256(modified.encode()).hexdigest())
    print("ONE_SYMBOL_ONE_LIST: YES")
    print("GLOBAL_LIMIT_70: YES")
    print("SYNTAX: PASS")
    return proposed

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default="/opt/bot-king-server/watchlist_store.py")
    ap.add_argument("--staging-dir",default="/opt/bot-king-backups/s18-stage")
    args=ap.parse_args()
    stage_file(args.source,args.staging_dir)
