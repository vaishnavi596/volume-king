#!/usr/bin/env python3
"""One-run BOT KING V2 source gap report and safety gate (never deploys).

Default is report-only when product acceptance remains pending; unsafe legacy
imports and missing essential modules fail closed. --strict also fails while
any device/transport acceptance remains unverified.
"""
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "src"
V2 = ROOT / "pilot_v2" / "android_app" / "src"
STAGED = ROOT / "pilot_v2" / "v1_clean_staging"
REPORT = ROOT / "pilot_v2" / "migration_report.md"
ACTIVE_REQUIRED = (
    "main.py", "app_state.py", "smart_data.py", "refresh_intent.py",
    "candle_history.py", "dashboard_parity.py", "watchlist_parity.py",
    "scanner_engine.py", "chart_indicators.py", "historical_migration.py",
    "analysis_quality.py", "candle_retention.py", "dhan_three_minute.py",
    "local_paper_slots.py", "local_notices.py", "evidence_inbox.py",
    "historical_three_minute_fallback.py",
)
STAGED_REQUIRED = ("five_engine.py",)
BANNED_IMPORTS = {
    "market_feed", "server_feed", "secure_credentials",
    "oracle_226_client", "oracle_device_login_226",
    "android_device_auth_226", "yfinance", "yahoo_fin",
}
# Only inspect actual AST imports and live executable calls, not text in comments.
BANNED_CALLS = {"ServerAngelFeed", "get_yahoo"}
EXTERNAL_GATES = (
    "V1 full screen, rich chart/WebView and physical Android acceptance",
    "Trusted live five-filter / Super Five / News / Futures evidence",
    "Real selected expiry CE/PE/OI/PCR/max pain Dhan observations",
    "True shared budget and data-only transport refresh implementation",
    "Master plus three delegate end-to-end phone authorization",
    "Nonexecuting V1 PAPER ledger and market alert parity",
    "Signed separate V2 candidate and Android installation",
    "Authorized Dhan-to-Oracle-to-V2 production verification",
)

def audit():
    if not V1.is_dir() or not V2.is_dir():
        raise RuntimeError("Source root missing: read-only V1 and V2 required")
    issues = []
    for name in ACTIVE_REQUIRED:
        if not (V2 / name).is_file():
            issues.append("Missing active V2 module: " + name)
    for name in STAGED_REQUIRED:
        if not (STAGED / name).is_file():
            issues.append("Missing quarantined clean V1 engine: " + name)
    py_files = sorted(V2.glob("*.py"))
    for path in py_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        except (SyntaxError, UnicodeError) as exc:
            issues.append("Invalid V2 syntax/encoding in " + path.name + ": " + str(exc))
            continue
        for node in ast.walk(tree):
            imports = ()
            if isinstance(node, ast.Import):
                imports = tuple(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports = (node.module.split(".")[0],)
            for imported in imports:
                if imported in BANNED_IMPORTS:
                    issues.append("Blocked import: " + path.name + " -> " + imported)
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else None
                if name in BANNED_CALLS:
                    issues.append("Blocked legacy call: " + path.name + " -> " + name)
    source = (V2 / "main.py").read_text(encoding="utf-8") if (V2 / "main.py").is_file() else ""
    wired = {
        "Watchlist + 70 unique equity selection": "LocalWatchlists" in source and "watchlist_rows(" in source,
        "3 independent dashboard indices": "index_card_model(" in source and "INDEXES" in source,
        "Scanner + Super Five shared historical chart": "scanner_history = HistoricalThreeMinuteFallback(" in source and "historical_shortlist(" in source,
        "Five source-gated filter slots and sixth blank": "filter_evidence.rows(" in source and "Sixth filter: reserved / blank" in source,
        "Verified-expiry options UI presentation": "expiry_choices." in source and "option_strikes" in source,
        "App-owned selected-demand manual request preview": "make_refresh_intent(" in source and "manual=True" in source,
        "PAPER preview / local five slots": "preview_manual_paper_risk(" in source and "LocalPaperPlanSlots" in source,
    }
    return {
        "issues": issues,
        "wired": wired,
        "pending_external": EXTERNAL_GATES,
        "legacy_module_count": len(tuple(V1.glob("*.py"))),
        "active_module_count": len(py_files),
    }

def write_report(result, *, strict=False):
    issues, wired = result["issues"], result["wired"]
    not_wired = [name for name, yes in wired.items() if not yes]
    blocked = bool(issues or not_wired or result["pending_external"])
    lines = [
        "# BOT KING V2 — Single-Run Delta Migration Audit",
        "",
        f"- Legacy V1 modules inventoried, read only: {result['legacy_module_count']}",
        f"- Active V2 modules inspected: {result['active_module_count']}",
        f"- Security and required-file findings: {len(issues)}",
        f"- Source UI wiring observations: {sum(wired.values())}/{len(wired)}",
        f"- App + device + provider migration: {'NOT COMPLETE' if blocked else 'COMPLETE'}",
        "- Audit does not migrate files, request live data, change V1, edit Oracle, or build APK.",
        "",
        "## Unsafe or missing source modules",
        *("- " + item for item in issues),
        *([] if issues else ["- No direct blocked imports/calls found in active V2 Python"]),
        "",
        "## Source-level UI reachability (not a runtime/device verdict)",
        *[f"- [{'x' if yes else ' '}] {name}" for name, yes in wired.items()],
        "",
        "## Separate mandatory acceptance still pending",
        *["- [ ] " + name for name in result["pending_external"]],
        "",
        "Source wiring checks are static heuristics, not proof that the application works.",
        "No secret material or Dhan/Oracle traffic is included in this report.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return bool(issues or (strict and blocked))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = audit()
    failed = write_report(result, strict=args.strict)
    print(REPORT.read_text(encoding="utf-8"))
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
