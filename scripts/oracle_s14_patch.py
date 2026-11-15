"""Stage a narrow S14 patch against the *running Oracle source*, never replace it.

Python >=3.9. No broker calls, no credential reads, no service restarts.
Usage: sudo python3 oracle_s14_patch.py --source /opt/bot-king-server/server.py
"""
import argparse
import ast
import hashlib
import os
from pathlib import Path
import re
import shutil
from datetime import datetime, timezone

OLD_OPTION = ('instrument = DHAN_VERIFIED_INSTRUMENTS.get(body.symbol)\n'
              '        if not instrument or instrument[2] != "INDEX" or instrument[0] != "IDX_I":')
NEW_OPTION = ('instrument = DYNAMIC_INSTRUMENTS.get(body.symbol)\n'
              '        if (not instrument or (instrument[0], instrument[2]) not in\n'
              '                (("IDX_I", "INDEX"), ("BSE_I", "INDEX"), ("NSE_EQ", "EQUITY"))):')

SELECTED_MODEL = '''class SelectedEquityBatchRequest(BaseModel):
    symbols: list[str]


'''

SELECTED_ROUTE = '''    @app.post("/dhan/selected-ltp-batch")
    def dhan_selected_ltp_batch(body: SelectedEquityBatchRequest,
                                x_botking_key: Optional[str] = Header(default=None)):
        """One authenticated, read-only Dhan request for 1..70 selected NSE equities."""
        if not x_botking_key or not hmac.compare_digest(
                x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        symbols = body.symbols
        if (not 1 <= len(symbols) <= 70
                or len(set(symbols)) != len(symbols)
                or any(not re.fullmatch(r"[A-Z0-9&_-]{1,32}", sym)
                       or DYNAMIC_INSTRUMENTS.get(sym, (None,))[0] != "NSE_EQ"
                       for sym in symbols)):
            raise HTTPException(422, "Unverified or excessive NSE equity selection")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        token = dhan_market_token()
        if not client or not token:
            raise HTTPException(503, "Dhan credentials not configured")
        pairs = [(DYNAMIC_INSTRUMENTS[sym][0], DYNAMIC_INSTRUMENTS[sym][1])
                 for sym in symbols]
        try:
            result = DhanFeed(client, token).batch_ltp(pairs)
        except DhanRateLimitError:
            raise HTTPException(429, "Dhan selected equity batch rate limited",
                                headers={"Retry-After": "30"}) from None
        except DhanFeedError:
            raise HTTPException(502, "Dhan selected equity quotes unavailable") from None
        entries = result.get("data", {}).get("NSE_EQ", {})
        if result.get("status") != "success" or not isinstance(entries, dict):
            raise HTTPException(502, "Invalid Dhan selected equity response")
        quotes, unavailable = {}, []
        for sym in symbols:
            try:
                raw = entries[str(DYNAMIC_INSTRUMENTS[sym][1])]["last_price"]
                if isinstance(raw, bool):
                    raise ValueError("Boolean quote")
                value = float(raw)
                if not math.isfinite(value) or value <= 0:
                    raise ValueError("Invalid quote")
                quotes[sym] = value
            except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
                unavailable.append(sym)
        if not quotes:
            raise HTTPException(502, "No valid selected Dhan equity quotes")
        return {"source": "dhan", "quotes": quotes, "unavailable": unavailable,
                "freshness": "unverified", "quote_timestamp": None,
                "live_orders_enabled": False}

'''

def make_stage(source):
    if not isinstance(source, str):
        raise ValueError("Source must be text")
    original_tree = ast.parse(source)
    names = {n.name for n in ast.walk(original_tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    needed = {"load_dynamic_instruments", "dhan_option_expiries",
              "dhan_option_chain", "dhan_ltp_batch", "dhan_index_ltp_batch"}
    if not needed.issubset(names):
        raise ValueError("Unknown server layout")
    if 'DYNAMIC_INSTRUMENTS = load_dynamic_instruments()' not in source:
        raise ValueError("Dynamic Registry initializer not verified")
    if '/dhan/selected-ltp-batch' in source or 'class SelectedEquityBatchRequest' in source:
        raise ValueError("Selected batch is already installed; no duplicate route")
    if source.count(OLD_OPTION) != 2:
        raise ValueError("Index-only guards have drifted; no automatic edits")
    if source.count('class DhanIntradayRequest(BaseModel):') != 1:
        raise ValueError("Pydantic model insertion point changed")
    if source.count('    @app.post("/dhan/ltp-batch")') != 1:
        raise ValueError("Batch insertion point changed")
    # Preserve all existing Oracle-specific Assessment / OI / cache logic.
    for marker in ('option_expiry_cache', 'calculate_oi_levels',
                   'build_assessment_snapshot', 'current_scope',
                   'live_orders_enabled', 'def load_dynamic_instruments'):
        if marker not in source:
            raise ValueError("Required Oracle feature missing: " + marker)
    staged = source.replace(OLD_OPTION, NEW_OPTION)
    staged = staged.replace('class DhanIntradayRequest(BaseModel):',
                            SELECTED_MODEL + 'class DhanIntradayRequest(BaseModel):', 1)
    staged = staged.replace('    @app.post("/dhan/ltp-batch")',
                            SELECTED_ROUTE + '    @app.post("/dhan/ltp-batch")', 1)
    if 'import re\n' not in staged:
        # Narrow insertion without touching other imports.
        staged = 'import re\n' + staged if not staged.startswith('"""') else (
            staged[:staged.find('"""', 3)+3] +
            '\nimport re' + staged[staged.find('"""', 3)+3:])
    ast.parse(staged)
    compile(staged, "oracle_s14_stage_server.py", "exec")
    tree = ast.parse(staged)
    routes = [n for n in ast.walk(tree)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              and n.name == 'dhan_selected_ltp_batch']
    if len(routes) != 1:
        raise ValueError("Expected exactly one staged batch")
    return staged


def stage_file(source_path, staging_dir):
    source_path = Path(source_path)
    staging_dir = Path(staging_dir)
    if not source_path.is_file():
        raise ValueError("No Oracle production server.py at path")
    source = source_path.read_text(encoding="utf-8")
    staged = make_stage(source)
    staging_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = staging_dir / ("server.s14.before." + timestamp + ".py")
    proposed = staging_dir / ("server.s14.proposed." + timestamp + ".py")
    if backup.exists() or proposed.exists():
        raise ValueError("Refusing to overwrite staged artifact")
    shutil.copy2(source_path, backup)
    proposed.write_text(staged, encoding="utf-8")
    os.chmod(proposed, 0o600)
    print("S14_STAGE_SUCCESS: YES")
    print("PRODUCTION_CHANGED: NO")
    print("SERVICE_RESTARTED: NO")
    print("PROPOSED:", proposed)
    print("BACKUP:", backup)
    print("ORIGINAL_SHA256:", hashlib.sha256(source.encode()).hexdigest())
    print("STAGED_SHA256:", hashlib.sha256(staged.encode()).hexdigest())
    print("OPTION_GUARDS_REPLACED: 2")
    print("SELECTED_BATCH_ADDED: 1")
    print("SYNTAX: PASS")
    print("DUPLICATE_SEARCH_ROUTE_ADDED: NO")
    return proposed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="/opt/bot-king-server/server.py")
    parser.add_argument("--staging-dir", default="/opt/bot-king-backups/s14-stage")
    arguments = parser.parse_args()
    stage_file(arguments.source, arguments.staging_dir)
