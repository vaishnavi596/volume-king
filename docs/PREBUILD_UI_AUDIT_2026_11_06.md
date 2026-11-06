# BOT KING — pre-build compact UI and functionality audit (2026-11-06)

Scope: 36 user-provided mobile screenshots; preserve existing working functionality. **No APK build until explicit user command.**

## Verified repository facts
- Flet application entry: `src/main.py`; app metadata: `pyproject.toml` (BOT KING 2.0.4).
- Data health status: `src/feed_health.py`.
- A stale response previously advanced `last_success`, making stale data appear newly refreshed. Fixed with a focused regression test.
- Existing `AUDIT_V2_0_0.md` describes previous offline tests, but not verification on the user's device.

## UI acceptance criteria before build
- Compact typography: page title ~16–18sp; section titles ~13–15sp; buttons ~11–13sp; preserve legibility and accessibility.
- Remove repeated page titles, duplicate navigation, and redundant labels, but retain required legal, safety, and status messages.
- Keep fixed bottom navigation and avoid horizontal overflow.
- Dashboard: summary of feed freshness, scanner results, paper orders, alerts; audit any prominently displayed Login control and its destination.
- Error indicator: show meaningful severity, timestamp, safe error explanation and actionable Retry/details only when handler exists. Never show an inactive decorative error control.
- Watchlist: only watchlist actions; validate list selection, search, add/remove, persistence, and stock-detail navigation.
- Chart: chart-specific controls only; validate candle/line toggle, timeframe, indicators, filter Apply, and drawing.
- Scanner: selected symbol, refresh/freshness, ranking, and explicitly unavailable option-chain data when feed lacks it.
- Settings: broker configuration, data source, demo/live, persistence; do not show secrets in error text.
- Every visible button must have a working handler, disabled state with explanation, or be presented as non-interactive text.

## Audit gates still outstanding
- Review actual `src/main.py` UI construction and event handlers section by section.
- Check all 36 screenshots against actual widget layout; no screenshot-by-screenshot mapping has yet been independently validated in this audit.
- Run source compilation and offline tests after all code edits; check Android device/WebView behavior after user authorizes build.
- Confirm package identifier and signing compatibility before claiming the APK will install as an update.
- Do not delete `new-version/` or other apparently unused files until imports, workflow references and history have been checked.

## Build gate
Do not invoke GitHub Actions, create APK, or change signing/package identity without user instruction.
