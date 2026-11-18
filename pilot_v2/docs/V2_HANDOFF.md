> **VERIFIED V2 V2-FT2-DASHBOARD-WATCHLIST-CI64-CI65-VERIFIED-20261118:** Exact UI batches #64 at `02cb519b` [201/201 PASS](https://github.com/vaishnavi596/volume-king/actions/runs/44347256520), #65 at `74240d45` [205/205 PASS](https://github.com/vaishnavi596/volume-king/actions/runs/44347701853). Dashboard compact three index cards, Watchlist compact selected-equity 3m rows/five evidence statuses and last-good quote; Master UI still status-only. **Offline source/unit PASS, no real Android visual/live/Oracle/APK acceptance.** No old V1 writes. **NEXT:** app-first FT2-P3 Scanner/chart/Super Five bounded parity segment. Framework [V2 General](V2_GENERAL_FRAMEWORK_RULES.md). Master Log V2-FT2-DASHBOARD-WATCHLIST-CI64-CI65-VERIFIED-20261118.

> **CURRENT V2 V2-FT2-P2-COMPACT-WATCHLIST-3M-ROWS-20261118:** Previous V2 CI #64 exact `02cb519b` **201/201 PASS**. Watchlist V2-only app batch adds compact per-symbol quote HIST/WAIT + validated 3m completed candle + five-filter summary + safe Remove with last-good preserved and 70 unique demand. Four new offline tests, **new Pilot CI PENDING**. Source parity partial, runtime/Oracle/APK not accepted. NEXT exact new CI then Scanner/Super Five app-only batch. No V1 writes.

> **CURRENT V2 V2-FT1-P1-FT2-P1-FIRST-DASHBOARD-CARDS-20261118:** Previous V2 audit HEAD `4dc96811` docs-only, last source #63 197/197 PASS. First V2-only UI batch replaces plain NIFTY/BANKNIFTY/SENSEX price lines with compact validated index cards and 1m candle/five-filter statuses, plus truthful Master/health Settings labels; new four-case offline regression file. **NEW CI PENDING**, NOT live data or visual-device acceptance; no V1/Oracle/APK writes. NEXT exact CI check, then bounded Watchlist V1-parity rows. Canonical audit [parity inventory](V2_V1_PARITY_BATCH_AUDIT.md).

> **V2 PARITY AUDIT V2-V1-PARITY-READONLY-SOURCE-INVENTORY-20261118:** New source-based [V1→V2 parity checklist](V2_V1_PARITY_BATCH_AUDIT.md) read-only inspected V1 `src/main.py` and V2 Flet `main.py`/state. V2 is NOT yet a full V1 copy: Dashboard cards, scanner chart, Super Five, option-chain rows, Master controls, Error Doctor and AI result UI are still partial/placeholders. V2-only batches FT1-P1/FT2-P1 → FT2-P2 → FT2-P3/FT3-P1 → FT3-P2/3 → FT4 candidate APK then Oracle LAST. **No legacy writes.** Current last executable V2 #63 197/197 PASS, this audit docs-only. Framework [V2 General](V2_GENERAL_FRAMEWORK_RULES.md). NEXT: group first app UI parity implementation + offline tests. Tag V2-V1-PARITY-READONLY-SOURCE-INVENTORY-20261118.

> **OWNER CURRENT FRAMEWORK V2-OWNER-FINAL-SAME-COPY-APP-FIRST-V2-ONLY-20261118:** READ [**BOT KING V2 GENERAL / स्थायी नियम**](V2_GENERAL_FRAMEWORK_RULES.md) FIRST. V2 = V1 same screens, structure, features and UI experience, but independent app that owns all product settings/AI/refresh and gets Dhan-only market data through Oracle's protected technical pipeline. **NO further work/commits to V1 app, legacy branch or old journal**, only READ-ONLY parity reference. Owner order V2 app parity in grouped FT1–FT3 batches → full app regression → owner-approved V2 APK candidate/install → Oracle server adaptations LAST → protected live-data validation. 1 Master + up to 3 delegated phones; Master-authorized Dhan token reauth only when actually required. Low-click smart batching and exact CI, no needless per-file commits. Current isolated V2 #63 197/197 PASS at `dcf1db00`, actual phone/Oracle/APK NOT PASS. NEXT: V1→V2 parity inventory then app-first combined gap fixes. Journal tag V2-OWNER-FINAL-SAME-COPY-APP-FIRST-V2-ONLY-20261118.

> **VERIFIED V2 FT1 V2-FT1-ATOMIC-P256-HTTP-CI63-VERIFIED-20261118:** Exact `dcf1db00` [V2 CI #63](https://github.com/vaishnavi596/volume-king/actions/runs/44343869624) **197/197 PASS**, previous #62 **192/192 PASS**. Atomic P-256 challenge-to-session **HTTP shell disabled by default**, strict HTTPS scope, mandatory test rate gate, replay/invalid signature denied. This does NOT implement native Keystore, verified master enrollment, deployed Oracle TLS/rate limiter or real phone login. **NEXT:** combined synthetic issuer → app HTTPS reader bearer handoff and revoked/expired authorization safety tests, then genuine verified device integration. No APK/Oracle production. Full V2 Master Journal V2-FT1-ATOMIC-P256-HTTP-CI63-VERIFIED-20261118.

> **CURRENT V2 FT1 V2-FT1-ATOMIC-P256-HTTP-LOGIN-SHELL-20261118:** Prior V2 #62 `3caac51c` 192/192 PASS, docs-only HEAD `e535aa15`. New disabled-by-default separate atomic P-256 challenge → server-verified short-lived bearer HTTP shell, strict HTTPS scope/mandatory rate gate/no master bootstrap endpoint + synthetic FastAPI tests. **NEW V2 CI PENDING**. No live Android login, real Oracle, durable production rate-limiter or APK. **NEXT:** read exact resulting Pilot CI and fix if red; if green, plan protected device bearer handoff to read-only HTTPS reader. Full Master Journal V2-FT1-ATOMIC-P256-HTTP-LOGIN-SHELL-20261118.

> **VERIFIED V2 FT2 V2-FT2-HTTPS-READER-CI62-VERIFIED-20261118:** Source `3caac51c` [Pilot CI #62](https://github.com/vaishnavi596/volume-king/actions/runs/44342986738) **192/192 PASS**, after #61 187/187 PASS. HTTPS-only GET V2 quote/index adapter (no redirects, no HTTP fallback, TLS verification, last-good preserved) passed OFFLINE mocked tests only. Actual master-approved native Android login, authenticated HTTPS session issuance and Oracle integration still NOT IMPLEMENTED; no production change or APK. **NEXT:** FT1/FT2 secure device proof/session issuance boundary, then legitimate client wiring with verified origin. Full V2 Master Journal V2-FT2-HTTPS-READER-CI62-VERIFIED-20261118.

> **CURRENT V2 FT2 V2-FT2-ANDROID-HTTPS-READONLY-CLIENT-20261118:** Last executable V2 #61 `64e9970b` 187/187 PASS, docs HEAD `c23af8cf`. New isolated HTTPS-only read client for signed-in *future* device bearer, strict exact V2 quote/index GET, TLS verification/no redirect, no HTTP fallback, <=64KB JSON, masked failures + last-good cache; new mocked transport tests. **PILOT CI PENDING**, no live login, no Oracle/Dhan/API-token interaction, no APK. **NEXT:** check exact new CI first, then bounded native/session bootstrap/security integration. Master Journal V2-FT2-ANDROID-HTTPS-READONLY-CLIENT-20261118.

> **VERIFIED V2 FT2 V2-FT2-READ-DELIVERY-CI61-VERIFIED-20261118:** V2 Pilot exact `64e9970b` [CI #61](https://github.com/vaishnavi596/volume-king/actions/runs/44342023400) **SUCCESS, 187/187 isolated tests**; previous V2 #60 **183/183 PASS**. Read-only HTTP response gate retains last-good on denied 401/403/expired/invalid transport; direct authenticated Android HTTPS client STILL NOT IMPLEMENTED, boolean is not cryptographic login proof. **NEXT:** bounded native/session-authenticated client design and source integration, no Oracle production, no signed APK, no live Dhan/trades. Master Journal V2-FT2-READ-DELIVERY-CI61-VERIFIED-20261118.

> **CURRENT V2 FT2/FT3 V2-FT2-FT3-PROTECTED-READ-DELIVERY-20261118:** Previous V2 #60 183/183 PASS at `4ce02291` and docs-only HEAD `ac0c8eed`. New isolated read-only HTTP 200 + authenticated-session-attested response → Flet `DeviceFeedInbox` guard with TestClient security/last-good tests. No actual HTTPS session implementation, no live data, no Oracle or APK. **NEW V2 CI PENDING.** Next verify exact Pilot CI, fix concrete failure before dependent development. Master Journal V2-FT2-FT3-PROTECTED-READ-DELIVERY-20261118.

> **VERIFIED V2 FT3 V2-FT3-EVIDENCE-INBOX-CI60-VERIFIED-20261118:** V2 Pilot exact `4ce02291` [CI #60](https://github.com/vaishnavi596/volume-king/actions/runs/44341060561) **183/183 PASS**, previous #59 **178/178 PASS**. App-owned unified `DeviceEvidenceInbox` connects Flet's local Candle/Options/Five-Filter cache state to strict symbol/timeframe/observation/expiry contracts; sixth slot blank. **LOCAL OFFLINE GATE CLOSED, runtime/authenticated transport/device/APK still OPEN.** No Oracle production writes, Dhan calls, renewal, orders or APK. **NEXT:** bounded FT2/FT3 authenticated read-only transport → Flet source integration gate; read latest actual V2 commit/CI first. Canonical Master Journal V2-FT3-EVIDENCE-INBOX-CI60-VERIFIED-20261118.

> **CURRENT V2 FT3 V2-FT3-UNIFIED-APP-EVIDENCE-INBOX-20261118:** Prior #59 178/178 PASS at `6b711005`, latest previous V2 HEAD `0ed55972` docs-only. Joint app source now shares one `DeviceEvidenceInbox` for validated candles, selected expiries, options and five evidence-gated filters (sixth blank) with Flet display and roster removal. Added isolated joint tests. **New exact Pilot CI PENDING**; this is NOT authenticated network/Dhan runtime or signed APK. **NEXT:** inspect new exact V2 CI and fix any actual failures before opening subsequent FT3 transport milestone. Master Journal V2-FT3-UNIFIED-APP-EVIDENCE-INBOX-20261118.

> **VERIFIED V2 FT3 V2-FT3-EXACT-CANDLE-JOIN-CI59-VERIFIED-20261118:** Exact V2-only commit `6b711005` [CI #59](https://github.com/vaishnavi596/volume-king/actions/runs/44339932591) **SUCCESS, 178/178 isolated tests**; previous #58 174/174 PASS. New optional candle_trend evidence join requires same last completed bar/source/trusted client, no invented bullish/bearish. Flet data ingress still NOT wired; Oracle/Dhan/device/APK NOT verified. **NEXT:** bounded FT3 Flet evidence-inbox ownership and validation gate, using #59 as prior PASS; keep app settings app-owned and Oracle transport-only. Canonical V2 Master Journal V2-FT3-EXACT-CANDLE-JOIN-CI59-VERIFIED-20261118.

> **CURRENT FT3 V2-FT3-CANDLE-FILTER-EXACT-BAR-JOIN-20261118:** Dedicated V2 branch prior HEAD `0693e2e6`, last code CI #58 at 56d8103 **174 isolated PASS**. New grouped app-only **completed candle → candle_trend observed_at exact-last-bar matching gate** plus offline tests; this prevents future cross-timeframe, stale bar and untrusted factor joins without inventing B/S signals. V2 PILOT CI FOR THIS BATCH **PENDING**. Code is not yet live UI/API wiring, signed APK or Oracle deployment. **NEXT:** inspect exact new Pilot CI; on green continue bounded FT3 evidence integration gate; on red fix concrete failure first. Full Master Journal tag V2-FT3-CANDLE-FILTER-EXACT-BAR-JOIN-20261118.

> **CURRENT V2 GENERAL HANDOFF V2-OWNER-GENERAL-SCOPE-CORRECTION-20261118:** Work ONLY on dedicated `pilot/botking-v2-smart-gateway-20261118` / `pilot_v2/` (not legacy BOT KING branch or `src/main.py`). Exact V2 source `56d8103` CI **#58 44333928669 SUCCESS / 174 isolated tests**; initial docs HEAD `9d9ee5f9`. Legacy Android full CI #1961 SUCCESS is **NOT V2**. Owner architecture: app owns 70 selected equities+3 indices, Smart Data/timeframes, five filters+blank sixth, Scanner/Super Five, 1–4 devices; Oracle only Dhan token/auth+secure transport, provider-safe quota and minimal shared dedup. Present V2 source cap of 3 devices is OPEN for later prebuild combined review; no phone/Oracle/APK claim. **NEXT:** inspect most recent V2 commit+CI, then proceed with FT3 candle/filter observation/delivery-contract joint segment; batch genuine related changes. GitHub Discussions General direct posting unavailable through current connector; this is V2 canonical GitHub journal/handoff. Master Journal tag V2-OWNER-GENERAL-SCOPE-CORRECTION-20261118.

> **VERIFIED V2-FT3-CANDLE-REPLAY-CI58-VERIFIED-20261118:** FT3 last completed candle rollback protection source `56d8103` CI #58 `44333928669` SUCCESS. Real Dhan/Android not tested; release HOLD. Next offline FT3 source-contract audit. No Oracle/APK/token actions.

> **CURRENT V2-JOINT-FT3-CANDLE-LAST-TIMESTAMP-REPLAY-GATE-20261118:** New offline per-symbol/timeframe last completed candle timestamp replay protection + regression tests committed, CI PENDING. Previous source #57 PASS. No Oracle/Dhan/APK operation.

> **VERIFIED V2-FT3-OBSERVATION-CI57-VERIFIED-20261118:** FT3 option/five-filter observation rollback guard exact SHA `7a862c8` CI #57 `44333231344` SUCCESS; per-factor last-good, no false LIVE. FT1–FT4 real phone/Oracle/Dhan/APK gates still BLOCKED. Next offline batch only.

> **CURRENT V2-FT3-OBSERVATION-MONOTONIC-REPLAY-GUARD-20261118:** New FT3 source-time rollback protections for options and each of five filters; revision alone cannot overwrite later observation. Full/partial HIST retention tests committed; CI PENDING. Prior exact #56 PASS. No APK/Oracle/Dhan/token changes.

> **VERIFIED V2-FT3-CI54-FT4-CI55-FAIL-CI56-PASS-20261118:** FT3 #54 `44331493500` PASS; FT4 #55 `44332135404` FAILED static regex, corrected exact SHA `17719e68` #56 `44332468618` SUCCESS. Future coordinated V2 version bumps source-only permitted, actual APK release HOLD. No Oracle/Dhan/token/APK operations.

> **CURRENT V2-FT4-CI55-REGEX-ESCAPE-CORRECTION-20261118:** #55 FT4 source gate failed 3 tests due overescaped regex literal; corrected one source expression, new CI PENDING. Prior #54 PASS; no Oracle, APK, Dhan or token activity.

> **CURRENT V2-FT4-FUTURE-VERSION-INCREMENT-SOURCE-GATE-20261118:** FT4 static source version gate accepts future coordinated V2 2.0.101+ versionName/code only, never actual APK release; mismatches and rollback fail. Last FT3 #54 PASS. New CI pending, no server/APK/Dhan.

> **LATEST V2-FT3-OPTIONS-OBSERVATION-REVISION-CI54-SUCCESS-20261118:** FT3 option observation-to-filter retirement CI #54 `44331493500` SUCCESS exact source `16e5d2b`. Prior FT4 #53 PASS. No actual Dhan, Android, APK, Oracle or token changes. NEXT static FT4 versionCode future increment audit, release HOLD.

> **CURRENT V2-JOINT-FT3-OPTION-METRICS-REVISION-INVALIDATION-20261118:** FT3 app-only option-metrics revision wrapper now retires four derived filter directions only when selected expiry's material observation changes, preserves candle and last-good. Regression CI pending; previous #53 PASS. No server/Dhan/APK.

> **LATEST V2-FT4-VISIBLE-IDENTITY-CI53-SUCCESS-20261118:** FT4 app-visible version parity CI #53 SUCCESS exact d578abf. Next offline scoped source audit; APK/Oracle not authorized.

> **CURRENT V2-JOINT-FT4-APP-DISPLAY-VERSION-METADATA-PARITY-20261118:** FT4 offline app-visible version/metadata parity fix+tests pending CI; release remains HOLD and no APK/Oracle operations.

> **LATEST V2-JOINT-FT3-CI52-FT4-STATIC-SOURCE-REVIEW-20261118:** FT3 expiry-switch safe factor retirement exact CI #52 `44328405428` SUCCESS on `b69e4da`. FT4 source-only review confirms release HOLD; intended V2 metadata is NOT actual APK/phone proof and offline CI does NOT run Flet. Next sequential offline audit repairs; no Oracle/Dhan/APK operations.

> **CURRENT V2-JOINT-FT3-EXPIRY-CHANGE-OPTION-FACTOR-RETIREMENT-20261118:** offline expiry→filter invalidation on choice/roster change, preserves candle. CI pending; real provider and phone still blocked.

> **JOINT AUDIT VERIFIED #50/#51 SUCCESS:** FT1 revoke P256 trust+challenge cleanup CI #50 44326725753 exact c93cb50b. FT2 shared gateway→Flet mandatory schema_version fix CI #51 44327304001 exact ade224c. Both OFFLINE only. Next FT3, then FT4 audit. No Oracle, Dhan token or APK.

> **CURRENT FT2 SCHEMA PARITY:** shared read-only gateway payload lacked mandatory Flet schema_version 1. Source-only fix + direct shared→Flet test committed, CI PENDING. FT1 #50 PASS. NO APK/Oracle/Dhan token changes.

> **CURRENT FT1 #50 PASS:** #49 failed one test fixture, corrected resolver, exact source c93cb50b #50 SUCCESS; next FT2 source review and scoped correction; Oracle/APK prohibited.

> **FT1 V2-FT1-REVOKE-CI49-TEST-SETUP-FIX-20261118:** #49 FAIL fixture-only delegated verifier missing current key resolver; correction committed pending CI. No Oracle/Dhan/APK.

> **CURRENT V2-JOINT-FT1-REVOKE-TRUST-STATE-CLEANUP-20261118:** FT1 first audit-repair: revoke removes optional device trust/approval/login-challenge rows in one SQLite transaction; CI pending, Android login still BLOCKED, no host/APK operations.

> **VERIFIED V2 FT1–FT4 OFFLINE STATUS, 2026-11-18:** FT1 synthetic 4-device P256 #40 PASS; FT2 independent index/equity inbox + protected TestClient #41/#42 PASS; FT3 expiry/Smart Data/five filters/option metrics join #43–#47 PASS; FT4 no-APK release HOLD source gate #48 PASS exact 2300139a. ALL are offline code/CI only. **No APK build/sign, Oracle host action, Dhan call or token edit.** NEXT: one joint FT1→FT4 evidence/defect audit and correction per batch; actual Android Keystore login, HTTPS market-data producer, option source/filters and signed APK remain blocked.

> **CURRENT V2-FT4-RELEASE-HOLD-STATIC-SOURCE-GATE-20261118:** FT4 source-only prebuild gate explicitly release HOLD; no APK signed, server or Dhan changes. Source CI pending, next joint FT1–FT4 audit.

> **CURRENT V2-FT3-OPTION-FILTER-MATCHED-EXPIRY-SOURCE-GATE-20261118:** FT3 option/filter source-join matched expiry/observation tests pending CI, no real broker request. See journal.

> **LATEST FT3 #45/#46 SUCCESS:** Expiry source-gating and independent five-factor WAIT/HIST regression passed offline; actual Dhan, phone APK and Oracle not touched. Continue original FT1–FT4 owner schedule.

> **CURRENT V2-FT3-INDEPENDENT-FIVE-FACTOR-EVIDENCE-20261118:** FT3 independent five-filter partial-evidence test+code pending CI. Missing factors WAIT; no auto trading or real Dhan verified.

> **FT3 VERIFIED CI #45 (44323382080):** source bd48d56 SUCCESS for per-symbol trusted expiry roster / strict calendar dates; offline only, no live Dhan, APK or Oracle. Next FT3 filter readiness.

> **CURRENT V2-FT3-EXPIRY-SOURCE-GATED-CHOICE-20261118:** FT3 source-gated per-symbol option expiry choice, no auto-guessed expiry, full source CI pending. Native app/Oracle/Dhan untouched.

> **VERIFIED V2-FT3-OPTION-AND-REFRESH-CI43-CI44-PASS-20261118:** V2 FT3 source #43/#44 full CI PASS on exact 9ee326a/c650152; options metrics guarded, Smart Data local intent 0/5/51/70. No authenticated live source or APK. Next FT3 offline.

> **CURRENT V2-FT3-APP-REFRESH-INTENT-20261118:** FT3 options evidence CI #43 SUCCESS; Flet local no-network refresh intent code/test pending CI. Next verify, continue offline FT3, never server/APK yet.

> **CURRENT V2-FT3-OPTION-METRICS-CANDLE-FILTER-OFFLINE-20261118:** FT3 offline option-evidence normalization joined to candle/filter display without inventing signals; exact CI pending, no real Dhan/Oracle/APK.

> **LATEST V2-FT2-ISOLATED-FEED-CI41-CI42-SUCCESS-20261118:** exact source #41 and #42 full offline CI PASS for independent app quote/index revision lanes + protected synthetic HTTP→Flet joint test. Next FT3 offline joint data, no Oracle/APK.

> **FT2 V2-FT2-HTTP-FLET-DUAL-FEED-CI41-FOLLOWUP-20261118:** CI #41 PASS for app-only quote/index revision separation; protected mock Gateway→Flet dual-feed parity test pending full CI. Real Android/Oracle not deployed.

> **CURRENT V2-FT2-ISOLATED-INDEX-EQUITY-REVISION-INBOX-20261118:** FT2 two-lane equity/index revision isolation prepared in Flet with offline tests; CI pending, no real network. Owner restrictions remain.

> **FT1 V2-FT1-FOUR-DEVICE-CI40-SUCCESS-20261118:** Historical CI #38 FAIL corrected #39 PASS; latest full #40 SUCCESS at 6cc7d6e. Four-device P256 SQLite synthetic gate passed; real mobile auth blocked. Next FT2 offline.

> **FT1 V2-FT1-FOUR-DEVICE-CRYPTO-CROSS-WORKER-20261118:** #38 legacy test FAIL corrected, #39 PASS. Added signed P256 4-device two-worker test pending new CI; do not claim real login. No APK/Oracle.

> **CURRENT V2-FT1-FOUR-DEVICE-CI38-LEGACY-ASSERT-CORRECTION-20261118:** CI38 failed legacy 3-device assertion (135/136 passed); test corrected for 4-device policy; new CI pending. FT1 must pass before FT2.

> **CURRENT V2-FT1-FOUR-DEVICES-CONSISTENT-CAP-OFFLINE-20261118:** FT1 consistent four-device cap correction + updated offline tests, CI pending; native Android login still not proven. No server/APK.

> **JOINT AUDIT V2-JOINT-FT2-FT3-FT4-SOURCE-AUDIT-20261118:** FT1–FT4 source-only audit done, packet blockers itemized in Work Log/Master; no repair/deploy yet. Next owner-ordered FT1 scoped remediation; APK and Oracle host off limits.

> **JOINT AUDIT V2-JOINT-AUDIT-FT1-SECURITY-EVIDENCE-20261118:** FT1 source-only review PARTIAL; native login/bootstrap and 4-device mismatch queued. Next FT2 source audit, no server or APK. See Master/Work Log for evidence.

> **CURRENT V2-FT1-FT4-OFFLINE-PACKET-PREFLIGHT-20261118:** FT2 #35 + FT3 #36/#37 all source CI PASS. FT4 offline identity/release-hold inventory recorded, APK/server strictly NOT attempted. Next FT1→FT4 combined audit, scoped repairs sequentially; latest journal entry in V2 Work Log.

> **CURRENT V2-FT3-CANDLE-OPTIONS-FILTER-EVIDENCE-JOINT-OFFLINE-20261118:** FT3 candle/options/filter evidence dependency offline CI pending; FT1–FT4 preparation only, no APK/server/Dhan operations.

> **CURRENT V2-FT3-APP-ROSTER-ONE-SHARED-QUOTE-LEASE-OFFLINE-20261118:** FT-3 owner-selected roster to shared synthetic SQLite quota lease integrated test pending CI. NO Oracle work or APK. Follow owner offline-then-joint-audit order.

> **CURRENT V2-FT2-PROTECTED-HTTP-FLET-JOINT-OFFLINE-20261118:** FT-2 protected HTTP and Flet end-to-end offline contract tests pending CI; no server or APK operations. Follow owner FT1→FT4 offline-first order.

> **VERIFIED V2-FT2-GATEWAY-FLET-PARITY-CI34-SUCCESS-20261118:** FT2 frozen schema parity CI #34 PASS at f5191e9; owner forbids server activity/APK now. Continue remaining offline FT2 and FT3 contracts, then joint staged audit.

> **CURRENT OWNER ORDER V2-OWNER-FT1-FT4-OFFLINE-FIRST-ROUND-BY-ROUND-20261118:** FT1→FT4 offline pattern first; NO server work, NO APK. Afterward joint audit and correct batch by batch. FT-2 frozen gateway/Flet parity test pending CI; see V2 Work Log.

> **LATEST V2-S3-FILTER-WATCHLIST-CI33-SUCCESS-20261118:** full V2 offline CI #33 PASS at cf4ecf1; five filters shared for three app surfaces, blank sixth. Live/mobile not verified.

> **CURRENT V2-S3-SHARED-FILTER-WATCHLIST-20261118:** Shared five-filter engine added to Watchlist 3m with offline tests; exact CI pending, no live source.

> **CURRENT V2-S3-FIVE-EVIDENCE-FILTER-WAIT-20261118:** five evidence-gated filter slots + blank sixth; pure offline module/UI and tests, exact CI pending. No real source integration.

> **LATEST V2-S3-LOCAL-CANDLE-CI31-SUCCESS-20261118:** V2 #31 full offline CI PASS exact 774e44a, local 1m/3m/5m completed-candle retention. Continue S3 filter/UI, no Oracle/server changes.

> **CURRENT V2-S3-APP-LOCAL-VALIDATED-CANDLE-RETENTION-20261118:** app-local normalized completed candle evidence validation, retention and WAIT/HIST summaries; CI pending. No live history adapter or actual chart yet.

> **LATEST V2-S3-READONLY-QUOTE-CI30-PASS-20261118:** exact full pilot CI #30 SUCCESS at 3e00adf, device-local read-only quote view; no live transport. Continue current app-first S3 candle/filter scope.

> **CURRENT V2-S3-READONLY-DEVICE-QUOTE-CONSUMER-20261118:** Flet local schema-validated quote view + synthetic regression, CI pending; no actual quote transport. Continue app-first without changing server/token.

> **LATEST V2-FAST-CI28-CI29-SUCCESS-20261118:** exact V2 source #28 and #29 PASS. Current branch app-local Smart Data + Scanner controls implemented; offline CI only, next S3 validated data consumer. No Dhan/Oracle changes.

> **CURRENT V2-S3-FLET-SCANNER-LOCAL-SELECTION-20261118:** Flet app-local Scanner selectors + tests committed pending CI; no broker requests or invented signals. Previous V2 CI #28 SUCCESS.

> **CURRENT V2-S3-APP-OWNED-SMART-DATA-SETTINGS-20261118:** app-only local Smart Data policy/config + synthetic tests; no active network polling; CI pending. Existing Flet V2 branch, no server auth change.

> **LATEST V2-S3-DEVICE-PERSISTENCE-CI27-SUCCESS-20261118:** V2 local Watchlist save source SHA 58ea34f CI #27 SUCCESS; Flet device run/Android install not yet tested. Next existing app batch.

> **CURRENT V2-S3-FLET-DEVICE-LOCAL-WATCHLIST-PERSISTENCE-20261118:** Local V2 Flet Watchlist saved-state roundtrip and fail-closed restore code/test committed pending CI. No server-side app settings. See V2 Work Log.

> **CURRENT V2-S3-FLET-LOCAL-SCREENS-WATCHLIST-20261118:** App-first offline Flet Dashboard/Watchlist/Settings and local 70-symbol selection code with synthetic tests; source CI pending. No live gateway or phone proof.

> **CURRENT SMART CI RULE V2-SMART-FAST-TRACK-CI-EFFICIENCY-RULE-20261118:** Existing V2 CI ~15–18s; apply one-change-batch/one-commit/one-full-gate, avoid redundant fetches/docs CI, preserve final APK safety test. Exact proof in V2 Master/Work Log.

> **LATEST V2-OWNER-AUTH-FREEZE-FINAL-JOINT-AUDIT-20261118:** Existing Dhan login/token renewal FROZEN; app work continues. Log defects without piecemeal edits; one final combined pre-build audit/fix/test batch, then APK. Details in V2 current status/Master/Work Log.

> **FIRST READ OWNER FINAL V2-OWNER-APP-CONTROL-ORACLE-TRANSPORT-ONLY-20261118:** Oracle holds no V2 product settings. All choices/Smart Control are in Flet V2 app; Oracle retains only Dhan connection/eligible renewal and necessary secure shared transport. Same branch; complete current app batch, tests, APK before Oracle phase. Full exact instruction in V2 Master Journal/Work Log; prior contrary proposals superseded, historical evidence preserved.\n\n> **CURRENT S1-READINESS-DURABLE-LEASE-INTEGRATION:** Previous V2 source `6154f460` exact CI #24 `44304560985` SUCCESS. New offline `staged_collector_scheduler.py` joins fail-closed Oracle/Dhan capability planning with SQLite worker-shared rate leases, preserving separate equity/index lanes and 429 cooldown. New CI pending. **This schedules synthetic work only**, never makes Dhan/Oracle requests; actual Oracle preflight and broker entitlement unverified. Next inspect CI, then authorized operator read-only inventory; no live deployment.

> **CURRENT S1 S1-DHAN-CAPABILITY-FAIL-CLOSED-20261118:** Previous source `d8fe238` exact #23 CI PASS; latest previous docs-only commit `98b099f` has no source CI by design. Added offline-only `collector_readiness.py` and tests that require explicit observed Oracle evidence, broker auth and independent equity/index entitlement before even building a trusted provider work plan. No real Oracle report has been collected; capability booleans in tests are synthetic. New source CI pending. NEXT inspect CI, then authorized read-only Oracle operator audit before live provider integration.

> **CURRENT START HERE — V2-CATEGORY-CONTINUITY-20261118:** Read [V2_LIVE_STATUS_AND_SCHEDULE.md](V2_LIVE_STATUS_AND_SCHEDULE.md) FIRST for category-wise completed work, observed CI #23 PASS on `d8fe238d95d9f9fbf51453005f7a82589d0c98ec`, exact pending S1–S5 schedule and routine "OK" workflow. This journal-only update changes no V2 source or Oracle host. Latest source remains V2 #23 PASS; historical LATEST banners below are archival.

> **LATEST FT2-ORACLE-PREFLIGHT-APK-GATE-20261118:** Previous commit `33c45eef` V2 CI #22 `44302157577` SUCCESS. Added a READ-ONLY Oracle source/service preflight script, V2 standalone APK identity gate (prebuild only) and synthetic tests, plus one operator guide. New CI pending. No Oracle host connection, Dhan token/quote calls, APK build or old-app changes. **NEXT:** verify CI, then capture a real read-only Oracle report via owner-approved host execution; build a dedicated V2 release pipeline only after confirmed app entry/identity/signing requirements.

> **LATEST FT-2-HTTP-OFF-V2-FLET-SHELL:** Verified immediately preceding `b705ff0` CI #21 `44301143072` SUCCESS. Added OFF-by-default read-only FastAPI GET quote/index shell and an independent Flet V2 offline source root, strict authenticated-feed tests and static V2 identity tests. New CI pending. NOT deployed to Oracle and NOT signed APK; real device pairing, Dhan feed and actual APK metadata remain unverified.

> **LATEST FT-2-API-MOCK-MOBILE-20261118:** Previous corrective source commit `ad5b84ef` CI #20 `44300533594` SUCCESS. Added pure versioned read-only `/v2-pilot` schema and matching Android-side fixture with 0/5/51/70 demand, three independent indexes, strict data validation and last-good cache. New CI pending. This is NOT a FastAPI HTTP endpoint or an Android APK. NEXT safe feature-flagged API shell + independent Flet Android identity and read-only Oracle preflight.

> **LATEST FT-1-ATOMIC-LOGIN-CI19-TEST-CORRECTION:** V2 #19 `44300289162` at `57e8d18` FAIL (73/74 PASS); the only error used the revoked original master token after new login rotated it. Targeted test fix updates self.owner to new session without changing security logic; corrective CI pending. Next verify CI before FT-2. No Oracle production/Dhan/APK changes.

> **LATEST FT-1-ATOMIC-LOGIN-ROTATION-20261118:** Prior V2 #18 run `44299581660` on `19746fb` SUCCESS. New `AtomicVerifiedLogin` combines nonce consumption, current P-256 key check and durable session creation under one SQLite BEGIN IMMEDIATE, preventing concurrent key rotation between proof and session issuance on the same local SQLite host. Synthetic cross-worker tests added. New CI pending. **No HTTP endpoint, production OAuth, Android Keystore implementation or APK**. Next verify exact CI; then FT-2 versioned read-only API mock and Android client contract, plus Oracle read-only readiness inventory.

> **LATEST FT-1-FASTER-CI-CURRENT-KEY-20261118:** Owner approved faster implementation; previous audit docs commit `24c3183` exact V2 CI #17 SUCCESS. Next mixed commit adds V2-only CI docs exclusion and current delegated P-256 key lookup during login, with tests across rotate/revoke. New CI pending. Caution: remaining verify-to-session issue race still blocks real HTTP. Continue with latest-only previous-commit/CI rule; no Oracle, broker or APK changes.

> **LATEST V2-FAST-TRACK-JOINT-EXECUTION-AUDIT-20261118:** Owner asked to audit speed and server/app integration; previous V2 source `b457316` had #16 SUCCESS. New `V2_FAST_TRACK_AUDIT.md` contains four packets: FT-1 current-key binding+CI path efficiency, FT-2 server API+Android contract in parallel, FT-3 Dhan collector/caches, FT-4 controlled Oracle deploy+independent signed APK. Updated stale Master Journal header. This audit is DOCUMENTATION ONLY; no Oracle, Android, Dhan or API functionality changed. **Next:** FT-1 implementation after this docs commit's exact applicable CI check. Earlier 10-file audit rule remains superseded.

> **LATEST V2-004D-DURABLE-KEY-LIFECYCLE:** Verified preceding docs-only commit `767f792` with V2 CI #15 SUCCESS. Introduced isolated atomic SQLite master-approved secondary P-256 public key enrollment/rotation with proof of possession, grants and session invalidation; new CI pending. **IMPORTANT OPEN SECURITY GATE:** Existing login verifier still takes static trusted key mapping; must wire `DurableDeviceKeys.public_key()` into login verification atomically before any HTTP exposure, or rotated old keys could authenticate. Master initial key/recovery and secure Android bridge remain separate. No production Oracle/Dhan/APK changes. Only previous commit files/CI rule applies.

> **LATEST RULE OVERRIDE (2026-11-18):** Check ONLY the immediately preceding V2 commit and the files it actually changed, plus its exact applicable CI result. PASS → continue; FAIL → fix then recheck. **No automatic 10-commit or 10-file checks.** Historical journal statements requiring ten are superseded. Previous source commit `5b736217`, CI #14 `44296710626`: SUCCESS. V2-004D cryptographic key lifecycle remains NEXT, not yet committed.

# BOT KING V2 — NEW CHAT HANDOFF (READ FIRST)
Updated: 2026-11-18
Project identification phrase: **"BOT KING IMPROVED V2 JOURNAL"** / **"बोट किंग इंप्रूव वर्जन का जर्नल देखो"**.

> **LATEST V2-OWNER-STANDING-WORKFLOW-20261118:** Owner authorizes routine V2 pilot-branch source/test/CI/journal continuation without repeated micro-approvals. New chat request "BOT KING V2 का काम जारी रखो" = verify HEAD+immediately previous commit's CI+this journal, then continue V2-002B. **CI #4** at `a020de855` SUCCESS, #3 failure corrected. Production/secret/Dhan consent/external device enrollment/orders/old app shutdown are NOT covered by blanket approval. No cross-chat background execution.

> **LATEST V2-002B-P256-TOKEN-STATUS (2026-11-18):** V2 CI #5 `44282742138` at `04c5c67` SUCCESS. Joint isolated P-256 challenge verifier + Dhan token status policy + real signature tests added (new exact CI PENDING); still no secure enrollment, multi-worker store, Android native Keystore integration or Oracle deploy. **NEXT:** verify new CI and continue V2-002 secure provisioning/auth readiness. No legacy, market orders or APK touched.

> **LATEST V2-002C-MASTER-ENROLLMENT:** Exact V2 CI #6 `44283251098` at `fa79f41` completed SUCCESS. V2-002C isolated master-approved secondary P-256 public-key enrollment with one-time challenge, read-only per-feed grants and max 3 device capacity added; new commit CI pending. Still NO HTTP endpoint, shared durable store, real Oracle deployment, client APK or actual device pairing. Next check exact CI and build atomic session/enrollment store before real auth.

> **LATEST V2-003A-SHARED-READ-ONLY-DELIVERY:** V2 CI #7 `44287980740` on `04e302485` SUCCESS. One mixed source+tests+Master Journal+Work Log commit adds offline `SharedQuoteGateway` for 1–3 devices and individually granted quotes/indices filtered through common last-good revision cache, with 0/5/51/70 display tests. New CI PENDING. Not a deployable server; no Dhan call, production write, V2 APK or old-app change. NEXT verify CI then V2-003B deduplicated demand and 429-safe collector and V2-002 production-safe auth.

> **LATEST V2-003B-GLOBAL-UNION-DEDUPE:** V2 CI #8 `44288336050` on `2b2c866` SUCCESS. New mixed source/tests/journals batch adds globally bounded (70 unique) deduplicated active demand across up to three enrolled mobile sessions, independent 3 indexes, removes disabled/revoked demand. Exact new CI pending. NOT deployed, no upstream collector, production auth or APK. NEXT verify CI and V2-003C broker-budget-safe coordinator and Oracle auth readiness.

> **LATEST V2-003C-QUOTE-BUDGET-429:** V2 CI #9 `44288636298` at `9aa16e1` SUCCESS. Added `quote_batch_coordinator.py` / tests: one active in-process read-only quote lease, >=1s global spacing, 60s per-symbol attempt spacing, cooldown_429, 70 equities + three index planning cap. CI for new SHA pending. Not integrated into an Oracle producer, and quote/index APIs are not assumed identical. NEXT exact CI then production-safe shared lease/store and V2 device authentication gates. No legacy/Oracle/Dhan/APK change.

> **LATEST V2-003D-SQLITE-SHARED-LEASE:** V2 CI #10 `44290170180` PASS at `fa408433`. New `durable_quote_gate.py` and tests implement SQLite single-host atomic quote work leases shared by multiple Python instances with persisted 429 cooldown, 60s per-symbol gap, 1s global gap and timeout recovery. New CI pending. **Prototype only**; no Dhan call, Oracle service change or APK. NEXT verify new CI then secure device auth durability and real Oracle Dhan readiness.

> **LATEST V2-004A-DURABLE-DEVICE-SESSION:** V2 #11 `44290644644` at `126e18db6f` SUCCESS. Added isolated SQLite durable device grants/hashed opaque sessions for 1–3 phones with atomic disable/revoke, worker-shared expiry/permissions and tests; new CI pending. NOT real Android/Oracle login; actual verified-key provisioning, backend API and Dhan token evidence still required. NEXT check new CI, bind cryptographic proof to durable authenticated gateway behind OFF flag. Old app and production untouched.

> **LATEST V2-004B-CRYPTO-DURABLE-LOGIN-COMPOSITION:** V2 CI #12 `44295202170` on `e81e0f4` SUCCESS. New `verified_login_gateway.py` composes real synthetic P-256 proof verification with SQLite durable per-device session auth, denies fake master and replay, cross-worker permission revocation; new CI pending. IMPORTANT: P-256 challenge store remains process-local; production needs atomic shared nonce and secure enrolled key lifecycle before any HTTP gateway. No Oracle/Dhan/APK changes. NEXT CI and atomic nonce store.

> **LATEST V2-004C-ATOMIC-CHALLENGE:** CI #13 `44295436072` PASS on `97f0ee2`. V2-004C adds `durable_challenges.py`, `test_durable_challenges.py` and login-gateway support for atomic SQLite one-time P-256 challenge consumption across workers. New CI PENDING. NO production Oracle, real mobile, Dhan login or APK. NEXT verify CI and implement secure owner-approved key enrollment/rotation + read-only Oracle auth inventory.

## 1. Start here, without requiring the owner to explain again
1. Read **`pilot_v2/docs/V2_HANDOFF.md`** (this file).
2. Read **`pilot_v2/docs/V2_MASTER_JOURNAL.md`**, then **`pilot_v2/docs/V2_WORK_LOG.md`** and `pilot_v2/README.md`.
3. Fetch newest branch HEAD and inspect **only immediately previous commit's changed files** and exact relevant CI result (plus any failed logs). Do not impose a ten-file/ten-commit sweep. If previous commit is docs-only, check the last applicable source CI separately. Journal status can be older than live GitHub.
4. Work in groups of 2–4 related safe edits and one atomic commit containing code, targeted tests, Master Journal, Work Log and a current handoff. Run targeted tests and exact-SHA full offline CI. The user's **"ok" means continue working**, not stop after a status note.
5. After each change, record WHY, WHAT, path/commit, tests/results and unresolved NEXT. Clearly distinguish offline code proof from Oracle deployed/Dhan live/device/APK.

## 2. Branches / scope
- **ACTIVE NEW WORK:** `pilot/botking-v2-smart-gateway-20261118` inside independent `pilot_v2/` folder, plus a dedicated V2 GitHub Actions test workflow.
- **LEGACY FROZEN FOR NEW FEATURES:** `fix/botking-joint-audit-70-15-20261115` remains preserved at V2 fork base `ecab2c223d8d15459c442c51c04aeda8cde7f9fa`. Preserve legacy source `src/`, `backend/`, legacy `pyproject.toml`, production Oracle and already installed Android app. Do not modify or deactivate old production just because V2 is in development.
- V2 **reserved** identity (not compiled, not installed): `com.botking.bot_king_v2` / version `2.0.100` / build code `100`, API prefix `/v2-pilot` **DISABLED**. Legacy app is `com.botking.bot_king`; current branch `pyproject.toml` version `2.3.130`; old build workflow builds legacy only.
- No V2 APK build until an isolated build+signing workflow genuinely sets a separate package, verifies actual APK metadata/certificate, and tests are PASS. Do not simply modify old `pyproject.toml` to build V2.
- Never copy auth secrets/tokens into GitHub or ordinary mobile preference stores.

## 3. Owner-approved destination architecture
- **Gateway 1 Dhan → Oracle:** Oracle safely owns Dhan OAuth/token lifecycle (only permitted renewal; existing oauth_consent previously reported `renewal_supported=false`, so owner browser reauth may be unavoidable), quote WebSocket and allowed REST fallback, 429 cooldown, stable shared collector/cache and revision timestamps. No promise of unlimited per-second data.
- **Gateway 2 Oracle → BOT KING V2:** HTTPS, independently authenticated revocable device sessions, verified master controls up to **3 phones including master's**; delegated phones get per-feed read-only permissions and optional enable/disable/revoke. Client-supplied `master` or device ID is NEVER authentication.
- **Master owner** has authorization to manage device enrollment and which data feeds each delegated device can see. No implicit remote phone control, unauthorized monitoring, order submission or exposure of main Dhan credentials to delegated phones.
- BOT KING V2 client manages 5 saved Watchlists with **max 70 unique equities total** (no duplicates across lists), independently 3 indexes, UI/timeframe needs, data-only refresh, evidence-gated five signals and sixth slot intentionally blank; scanner/filters/super five/options reuse shared validated cache. Hist/WAIT when provider evidence is missing.
- Android demand: Watchlist 3m candles, dashboard 1m index signals, selected scanner default 1m, Super Five 5m historical basis; trading hours auto data polling requested 09:10–15:45 IST (special NSE holidays need authoritative checking). Offline refresh manually when requested. At most read-only until separately authorized; live trading stays OFF.
- Eventually permit two/three phones to share one backend collector, instead of multiplying Dhan requests; Dhan account/market-data redistribution policies and entitlements must be verified.

## 4. What has ACTUALLY happened
- Branch created from saved legacy source HEAD `ecab2c2`.
- V2-001 commit **`577f07d9d9d45d50b3836bc12b5c3c334bd28375`** introduced ONLY isolated `pilot_v2/` domain contracts/tests/docs, `pilot_v2/pilot_identity.json` metadata and `.github/workflows/v2-pilot-contract.yml`; existing legacy code untouched.
- First dedicated GitHub Actions `BOT KING V2 Pilot Contract Tests` run **#1, ID 44281428941: completed SUCCESS** on exact `577f07d` commit.
- `pilot_v2/gateway_contract.py`: validated 0/5/51/70 distinct equity demand, 3 indexes, revision cache/last-good HIST/unverified, separate Dhan/app auth status; no HTTP.
- `pilot_v2/device_policy.py`: pure policy max 3, one master, delegated feed grants/disable/revoke; NOT a secure server login implementation. **Important:** `verified_bootstrap=True` is only a test-domain assertion; future server endpoint must verify authorized user and device credentials independently.
- `pilot_v2/tests/test_v2_pilot.py`: synthetic tests, **not production or device proof**.
- No Oracle changes/restart, broker calls, data subscription, APK, actual client screen, app pairing, mobile installation, live orders or API token changes.

## Most recent addendum (2026-11-18)
- V2 branch docs commit `bdb82cf821bfd5535c7f047ad98bd653d91d92b3` triggered separate V2 CI **#2 SUCCESS**, run `44281734585`; V2 code CI #1 also SUCCESS.
- V2-002A now adds isolated offline opaque per-device session manager + simulated proof verifier with master role derived server-side, token expiration/rotation/revocation and restricted per-feed permissions. **This is not a deployable login, lacks real cryptographic proof and durable/shared server session storage.** CI for source batch to be checked at new SHA.
- Continue at V2-002B after CI: cryptographic enrollment proof and token-life-cycle status; keep Oracle/old mobile untouched.

## CI #3 V2-002A error and correction
- Run #3 `44282334624` on `7c2c437` failed 1/10 due to raw mocked verifier TypeError on forged dictionary proof; 9 other tests passed. Correction intercepts malformed proof TypeError/ValueError as SessionDenied and adds test. Result for new commit pending until GitHub CI completion.

## 5. Exact next work / hard gates
**V2-002 (NEXT):** Read-only existing Oracle capability audit design and secure gateway contract. Inspect exact production SHA/routes/capability/active token type/expiry/renewal support without credentials or Dhan quote calls, through established safe operator route; current chat cannot assume SSH. Implement V2 server-side policy authentication and session-expiry tests in isolated `pilot_v2/`, behind feature flag, without writing production. Test forged master actor, revoked/expired device session, replay challenge and 4th-device denial.
**V2-003:** Shared upstream collector and per-device filtered revision cache, demand scaling 0/5/51/70+indexes, 429/422, stream disconnect, no double provider fanout across 2–3 phones. Underlying Dhan authorization may require real user consent.
**V2-004:** Data lanes candle/option/assessment with correct freshness, scanner/super five/five filters; six-slot UI with last blank.
**V2-005:** Native secure Android enrollment or approved secure alternative, separated Flet V2 package and signed build; verify actual APK versionCode/name/cert and install alongside legacy.
**V2-006:** Backup production, versioned feature-flag Oracle deployment, rollback simulation, health/auth smoke, V2 device acceptance, no legacy shutdown before PASS.

## 6. Safety and workflow
- Before new edits inspect just the immediately preceding commit's changed files and applicable CI, fixing FAILs first. Do not automatically inspect ten commits/files. Preserve one joint journal+test+source commit where possible.
- Never change `/opt/bot-king-server` based only on GitHub's `backend/server.py`. Production has different deployed source and credentials.
- Dhan OAuth renewal must honor provider rules; cannot automate an obligatory interactive consent by storing OTP or bypassing security.
- Everything is read-only; `live_orders_enabled=false`; never add real-order API exposure.
- Next reply to owner should succinctly say exact current V2 commit/CI, next batch and blockers, and **continue work** instead of repeating planning.
