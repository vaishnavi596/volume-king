# BOT KING — NEW CHAT HANDOFF — 2026-11-17
Repository: vaishnavi596/volume-king
Working branch: fix/botking-joint-audit-70-15-20261115
Primary journal: docs/BOT_KING_WORK_LOG.md
User prefers grouped 2–4 checks/changes per command, evidence-based status, journal every action, no image mockups, and no premature APK/deployment.

## Latest Oracle BK-5F operator output
Production /opt/bot-king-server/server.py: SYNTAX PASS, SHA256 c9577aafb00960a982e9782c9ab154ef2c944b39197740b53aac63d3cd81d625; assessment route count 0; all five filters and four factors NOT_FOUND within that route.
Isolated /tmp/bk_server_assessment_candidate.py: SYNTAX PASS, SHA256 8933088a70755182d97adadf82bbde5e1fe26d30d34b9de2a3c7cbda0b5d0f36; assessment route count 1; five filter IDs oi_support,oi_resistance,max_pain,pcr,candle_trend and factors news,futures,options,candle all DECLARED.
SOURCE_AUDIT_ONLY=true; LIVE_DATA_VERIFIED=false; DHAN_REQUESTS=0; PRODUCTION_CHANGED=false.
Candidate declaration is not proof of functional filter data or verified market freshness. Candidate is NOT deployed.
Earlier candidate synthetic tests: 9/9 isolated function tests + 6/6 FastAPI in-process ASGI tests = 15/15 PASS. FastAPI and Starlette available in Oracle venv, HTTPX unavailable. HTTP tests used synthetic key, no production import, no port or Dhan requests.

## Existing implementation
src/shared_assessment_ui.py strict fail-closed five-filter UI contract and four factor names; src/five_engine.py requires independent verified Dhan engine evidence and quorum; backend/dhan_option_metrics.py computes PCR/Max Pain and seven-listed-strike ATM window but marks freshness unverified and signal_eligible false.
B1 blockers: OI support/resistance functional mapping, verified expiry and chain freshness, independent completed-bar candle trend, Futures read-only acquisition, timestamped issuer-linked News and calibrated score. No fake bullish/bearish percentages; unavailable engines WAIT. Never enable live orders.
Tests-only commit 20e32ce452e53a2e8aee0a330de7d77036b27e10 added seven-strike boundary, invalid OI/optional fields, and fake freshness/eligibility regression tests. Latest observed GitHub workflow 43929936770 was in_progress on that commit; recheck before claiming pass.

## APK
Current pyproject.toml version 2.3.130. Proposed next test version 2.3.131, not committed or built. GitHub .github/workflows/build.yml includes versionName/versionCode/signing-certificate checks. Build a test APK after regression and security preflight, without claiming all five filters live. Check exact signed artifact and mobile install. One-phone smoke test: first login bootstrap, 51 equities and three independent index cards, Watchlist refresh/last-good retention, 3m candle consistency, Super Five, scanner, option chain, and after-hours manual refresh. No production changes or new APK verified yet.

## Immediate continuation
1. Recheck workflow 43929936770 and newest branch CI.
2. Plan grouped read-only Dhan/Oracle five-filter runtime verification; distinguish source declarations, calculations, actual provider availability and freshness.
3. Any candidate production deployment requires backups, explicit safety preflight, rollback and post-deploy health/auth checks. Never overwrite Oracle server.py from GitHub backend/server.py wholesale.
4. Update docs/BOT_KING_WORK_LOG.md with each result; this separate handoff was created because prior attempt to append the very large journal encountered a remote protocol disconnect.
