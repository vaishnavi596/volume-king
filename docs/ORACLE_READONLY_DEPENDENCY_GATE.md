# BOT KING — Oracle read-only dependency gate

**Status: operator execution pending.** This document is a runbook, not evidence that Oracle has been inspected. Do not paste credentials or the contents of `server.py` into chat or logs.

## 1. On the Oracle host (no restart, no write)

Use an SSH session already authorized for `bot-king-vnic`. Obtain the audited preflight script from the reviewed GitHub commit `b30555a98bb09f540ab42334dea3495d902ec7f4` through your normal secure checkout/deployment channel. Do not execute an unreviewed remote shell pipeline.

```sh
cd /opt/bot-king-server || exit 1
sha256sum server.py
python3 -B -c 'from pathlib import Path; p=Path("/path/to/reviewed/audit_oracle_candidate_dependencies_readonly.py"); compile(p.read_text(), str(p), "exec")'
python3 /path/to/reviewed/audit_oracle_candidate_dependencies_readonly.py --server /opt/bot-king-server/server.py
```

The compile-only command avoids creating `__pycache__`. The preflight reads `server.py` and emits only flags.

## 2. Interpret the sanitized result

- `sha_matches=true`, `factory_found=true`, and all four `binding_*=present` are required for `static_preflight=PASS`.
- Any `HOLD`, missing binding, SHA mismatch, syntax error, symlink, or unexpected output means **stop**. Do not update the expected SHA to silence a mismatch.
- A static PASS does **not** prove runtime imports, actual `pairing_key` value, middleware routing, or that five assessment filters have a working data producer.
- Do not post the `pairing_key`, `server.env`, OAuth credentials, Dhan tokens, full source, or HTTP authorization headers.

## 3. Next gates — not yet authorized

1. Independently inspect imports, scoping, decorator registration, and auth behavior in a disposable runtime staging environment.
2. Create and verify a separate backup of production `server.py` before any change.
3. Produce the SHA-pinned **candidate-only** file in a separate path, review its diff, and ensure the source is unchanged.
4. Only after a reviewed plan and successful protected loopback tests should any production deployment be considered.
5. The placeholder routes intentionally report unavailable/not-configured data. They do not implement five filters; no APK or live-order change is justified by their existence.

## Evidence to return

Only the sanitized preflight output and the SHA-256 of `server.py` (never secret values). Record the exact GitHub script commit, operator execution date, and pass/hold outcome in `docs/BOT_KING_WORK_LOG.md`.
