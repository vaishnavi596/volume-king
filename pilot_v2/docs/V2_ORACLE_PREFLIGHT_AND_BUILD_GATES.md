# V2 Oracle read-only preflight and independent APK gates

**Stage:** V2 source only. Production runtime has NOT been inspected or changed by this commit.

## Oracle authorized operator — read-only only
Copy the reviewed `pilot_v2/oracle_preflight.py` to an approved local staging path on Oracle and run:

```sh
python3 oracle_preflight.py --root /opt/bot-king-server --include-v2-service
```

It reports SHA-256 of allowlisted Python modules and selected `systemctl show` metadata for fixed `bot-king.service` and optional `bot-king-v2.service`, not env contents, token values, Dhan calls, health credentials, or device pairing keys. A different WorkingDirectory is a limited isolation indicator, NOT proof of separate ports, HTTPS mounts, service safety or production readiness. Share only its redacted JSON output. No deletion, backup, restarts, production writes or HTTP calls. A missing file is explicitly marked absent. This is one preflight evidence report, not a production readiness PASS.

## GitHub-only Android identity prebuild gate
```sh
python -m pilot_v2.android_build_gate --repo-root .
```
This compares V2 config and legacy metadata and checks release flags stay OFF. **It does not build, sign, inspect or install an APK.** A separate Flet V2 build workflow, signing credentials and final binary's package/versionCode/certificate verification are mandatory before pilot installation. Do not reuse the legacy root Flet build.

## Follow-up after preflight
Read actual Oracle source SHA and authenticated token-status capability without extracting secrets, confirm Dhan entitlements and routes, then stage a feature-flagged gateway behind existing HTTPS with backup/rollback; owner authorization required for live production actions.
