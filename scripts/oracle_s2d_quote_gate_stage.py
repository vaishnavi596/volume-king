"""S2D: stage a minimal Oracle Dhan LTP quote gate; NEVER deploy/restart.

Maintains the production-specific historical and option cooldown branches.
Fail closed unless the expected source layout is present. No credentials read.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import os
import shutil

CLASS_ANCHOR = "class DhanFeed:\n    _rate_lock = threading.Lock()\n"
POST_ANCHOR = "        try:\n            with self._opener(request, timeout=12) as response:\n                raw = response.read(2_000_001)\n"
REPLACE_POST = """        try:
            if endpoint == "/marketfeed/ltp":
                # Shared across all DhanFeed instances in this single-worker process.
                # Serialize the full request, with a 1.05s minimum start gap.
                gate = self._quote_lock
            else:
                gate = _nullcontext()
            with gate:
                if endpoint == "/marketfeed/ltp":
                    remaining = type(self)._quote_next_allowed - time.monotonic()
                    if remaining > 0:
                        time.sleep(remaining)
                    with self._rate_lock:
                        if time.monotonic() < DhanFeed._retry_after:
                            raise DhanRateLimitError("Dhan rate limit cooldown active")
                    type(self)._quote_next_allowed = (
                        time.monotonic() + self.QUOTE_MIN_INTERVAL_SECONDS)
                with self._opener(request, timeout=12) as response:
                    raw = response.read(2_000_001)
"""

def make_stage(source):
    if any(tag in source for tag in ("QUOTE_MIN_INTERVAL_SECONDS", "_quote_next_allowed", "_quote_lock")):
        raise ValueError("Quote gate already present or partially patched")
    tree = ast.parse(source)
    matches = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "DhanFeed"]
    if len(matches) != 1:
        raise ValueError("Expected one DhanFeed class")
    posts = [node for node in matches[0].body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_post"]
    if len(posts) != 1 or not isinstance(posts[0], ast.FunctionDef):
        raise ValueError("Expected one synchronous DhanFeed._post")
    if source.count(CLASS_ANCHOR) != 1 or source.count(POST_ANCHOR) != 1:
        raise ValueError("Oracle source layout differs; refuse patch")
    if "DhanFeed._historical_retry_after" not in source or "DhanFeed._option_retry_after" not in source:
        raise ValueError("Production-specific cooldowns missing; review required")
    if "with self._rate_lock:" not in (ast.get_source_segment(source, posts[0]) or ""):
        raise ValueError("Expected shared cooldown lock")
    if "from contextlib import nullcontext as _nullcontext" in source:
        raise ValueError("Unexpected prior partial patch")
    modified = source.replace("import json\n", "import json\nfrom contextlib import nullcontext as _nullcontext\n", 1)
    modified = modified.replace(CLASS_ANCHOR, CLASS_ANCHOR + """    _quote_lock = threading.Lock()
    _quote_next_allowed = 0.0
    QUOTE_MIN_INTERVAL_SECONDS = 1.05
""", 1)
    modified = modified.replace(POST_ANCHOR, REPLACE_POST, 1)
    ast.parse(modified)
    compile(modified, "dhan_feed.s2d.proposed.py", "exec")
    return modified

def stage_file(source_path, staging_dir):
    source_path, staging_dir = Path(source_path), Path(staging_dir)
    if not source_path.is_file() or source_path.is_symlink():
        raise ValueError("Expected regular non-symlink Oracle adapter")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    modified = make_stage(source)
    staging_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = staging_dir / ("dhan_feed.s2d.before." + stamp + ".py")
    proposed = staging_dir / ("dhan_feed.s2d.proposed." + stamp + ".py")
    if backup.exists() or proposed.exists():
        raise ValueError("Staging artifact collision")
    shutil.copy2(source_path, backup)
    proposed.write_text(modified, encoding="utf-8")
    os.chmod(proposed, 0o600)
    print("S2D_STAGE_PASS: YES")
    print("PRODUCTION_CHANGED: NO")
    print("BACKUP:", backup)
    print("PROPOSED:", proposed)
    print("ORIGINAL_SHA256:", hashlib.sha256(original).hexdigest())
    print("STAGED_SHA256:", hashlib.sha256(proposed.read_bytes()).hexdigest())
    print("PYTHON_SYNTAX: PASS")
    return proposed

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="/opt/bot-king-server/dhan_feed.py")
    p.add_argument("--staging-dir", default="/opt/bot-king-backups/s2d-stage")
    args = p.parse_args()
    stage_file(args.source, args.staging_dir)
