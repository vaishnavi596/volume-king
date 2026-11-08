# BOT KING retired-file archive

This directory is for **verified unused source files only**. It is not part of the active Flet application source (`src/`).

## Rules before moving a file here

1. Record original path, last active commit, reason for retirement, and restoration steps in this README.
2. Check imports, dynamic imports, tests, GitHub Actions, packaging assets, and Oracle deployment scripts for references.
3. Never move signing material, secrets, active configuration, migrations, or production backend files without a verified replacement.
4. Confirm tests and APK packaging exclude archived content. Moving a file alone is not proof of exclusion.
5. Preserve full history via Git commits; do not delete a source until a rollback path is documented.

## Retired files

None yet. Audit is ongoing; no file has been confirmed safe to retire.

### 2026-11-08 — Legacy standalone gateway

- Original: `new-version/bot_app.py`
- Archived copy: `archive/retired/bot_app_legacy_gateway.py.txt` (plain text; not importable as Python).
- Reason: historical standalone FastAPI gateway, not the configured Flet entry point (`src/main.py`) or Oracle installer entry point (`backend/server.py`). Provider gateway modules remain active because dedicated tests import them.
- Restore: copy archived text back to the original path and review against the current backend before use. Git history also preserves the original.
- Verification: static entry-point and installer review; complete automated regression suite and deployed Oracle state **not yet verified**.
