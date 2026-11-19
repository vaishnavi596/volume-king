#!/usr/bin/env python3
"""Read-only BOT KING V2 migration completion gate.

Never copies unsafe legacy code, alters V1, invokes providers, signs an APK,
edits Oracle, creates orders, or declares source-only tests as device PASS.
Run from the repository root. Use --strict to fail if any gate is open.
"""
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "src"
V2 = ROOT / "pilot_v2" / "android_app" / "src"
REPORT = ROOT / "pilot_v2" / "migration_report.md"
REQUIRED = (
    "main.py", "app_state.py", "smart_data.py", "candle_history.py",
    "dashboard_parity.py", "watchlist_parity.py", "scanner_engine.py",
    "chart_indicators.py", "historical_migration.py", "five_engine.py",
    "analysis_quality.py", "candle_retention.py", "dhan_three_minute.py",
    "local_paper_slots.py", "local_notices.py",
)
# Explicit evidence required from separate phone/data tests. Never auto-claim.
ACCEPTANCE = (
    ("Full V1 screen / WebView / layout and interaction parity", False),
    ("All five evidence-gated filters and Super Five source integration", False),
    ("Real CE/PE/expiry/OI/PCR/max pain, News/Futures provenance", False),
    ("App-owned data-only scheduled + manual Smart Data refresh", False),
    ("Master + 3 delegates end-to-end trusted device enforcement", False),
    ("Nonexecuting V1 Paper ledger + alert parity", False),
    ("Actual Android signed candidate and device visual acceptance", False),
    ("Authorized read-only Dhan/Oracle integration and live verification", False),
)
BLOCKED_IMPORTS = {"market_feed", "server_feed", "secure_credentials",
                   "oracle_226_client", "oracle_device_login_226",
                   "android_device_auth_226"}
BLOCKED_MARKERS = ("ServerAngelFeed", "get_yahoo(",
                   "import yfinance", "import yahoo_fin",
                   "from market_feed import", "from server_feed import")
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    issues = []
    assert V1.is_dir() and V2.is_dir(), "Expected V1 and V2 source trees"
    python_files = sorted(V2.glob("*.py"))
    for file in python_files:
        source = file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=file.name)
        except SyntaxError as exc:
            issues.append(f"Syntax error: {file.name}: {exc.msg}")
            continue
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [n.name.split(".")[0] for n in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split(".")[0]]
            for module in modules:
                if module in BLOCKED_IMPORTS:
                    issues.append(f"Legacy provider import: {file.name}: {module}")
        for marker in BLOCKED_MARKERS:
            if marker in source:
                issues.append(f"Legacy provider reference: {file.name}: {marker}")
    missing = [item for item in REQUIRED if not (V2 / item).is_file()]
    issues.extend("Missing active V2 module: " + x for x in missing)
    # Source is a distinct legacy product; do not mutate it as part of the run.
    legacy_count = len(list(V1.glob("*.py")))
    complete = not issues and all(verified for _, verified in ACCEPTANCE)
    lines = [
        "# BOT KING V2 — One-Click Migration Gate",
        "",
        f"- V1 Python modules scanned (read-only inventory): {legacy_count}",
        f"- Active V2 Python modules scanned (AST and provider boundaries): {len(python_files)}",
        f"- Missing required active modules: {len(missing)}",
        f"- Unsafe provider findings: {len(issues) - len(missing)}",
        f"- Migration completion: {'PASS' if complete else 'BLOCKED — NOT COMPLETE'}",
        "- No V1 writes, Oracle actions, Dhan calls, APK or order operations.",
        "",
        "## Source audit findings",
        *(["- " + issue for issue in issues] if issues else ["- No blocked legacy imports or marker references observed in active source"]),
        "",
        "## Required acceptance evidence (never inferred from offline tests)",
        *[f"- [{'x' if verified else ' '}] {name}" for name, verified in ACCEPTANCE],
        "",
        "## Interpretation",
        "This read-only workflow reports blockers. It cannot automatically assert missing "
        "live/provider/device evidence or safely blindly copy the legacy main.py.",
        "A green offline regression is not a completed V1-to-V2 product migration.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if args.strict and not complete:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
