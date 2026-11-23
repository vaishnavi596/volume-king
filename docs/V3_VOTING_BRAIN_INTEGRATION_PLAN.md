# BOT KING V3 — पाँच-बॉक्स Voting और छठे Brain का संयुक्त कार्य-अनुबंध
**तारीख:** 23 नवंबर 2026 | **स्थिति:** चरणबद्ध; पूरी LIVE wiring या server deployment का दावा नहीं

## नई प्रथम प्राथमिकता — 23 नवंबर 2026 (मालिक का निर्देश, V3)

**क्रम बदल गया है: अब 1 → 2 → 3; पहले छठे M Brain का server-side memory/backup आधार, फिर 17-filter wiring, फिर T/C/N/F/O independent engine wiring।** पुराने नीचे लिखे चरण A/B/C/D का तकनीकी सुरक्षा क्रम बना रहेगा, लेकिन यह नया कार्य-प्राथमिकता क्रम उनके ऊपर लागू है। वर्तमान B203 build/phone evidence अपना अलग in-flight acceptance है; उसे रद्द या अनावश्यक दोबारा ट्रिगर नहीं करना।

### 1 — BOX SIX / M Market Brain: सर्वर बैकअप और Memory Foundation (FIRST)
- Oracle Dhan pipe/token-renewal से पृथक **staging Brain Memory Service** का contract और read-only/inactive prototype पहले तैयार करना। Gateway के production routes/config/preferences में बदलाव नहीं; V1/V2 से पूर्ण अलगाव।
- Append-only authenticated `prediction_event`, `vote_evidence_reference`, `outcome_event`, `model_policy_version`; per-device phone 1–4 Master authorization, encryption, idempotency, revision and immutable audit trail। डिवाइस/सर्वर विफलता में bounded encrypted pending queue और replay।
- **बैकअप प्रथम:** encrypted versioned backups, restore verification, access audit, retention, reconciliation, server outage & four-phone conflicting event tests, recovery drill और rollback plan। किसी proof को केवल लिखे हुए contract से PASS न मानें।
- Proposed `/brain/v1/events`, `/brain/v1/sync`, `/brain/v1/health`, `/brain/v1/restore` staging-only; production Oracle deployment से पहले स्वतंत्र approval तथा server backup/safety gate। Secret, broker token, raw password, live trading access service को न मिले।
- **M Box की अवस्था:** अभी `STANDBY/WAIT`, **zero vote**; memory backup/auth/replay/4-phone PASS के बाद केवल read-only UI preview + Brain Sync Doctor। स्वतंत्र audit व user approval के बिना 5→6 voting quorum, autonomous weight changes या LIVE activation नहीं।

### 2 — सभी 17 Scanner Filters / Quality / Historical Analyzer (SECOND)
- 13 technical गणनाएँ + 4 OI context-only, 18th catalog option; zero false LIVE votes। NIFTY/BANKNIFTY/SENSEX/RELIANCE 1m, Watchlist 3m, 5m source-scoped cache; real timestamps, irregular spacing के actual causes; पिछले verified completed session से HIST analysis।
- Historical vs LIVE quality gates अलग; last-good retained, Volume provenance, expiry-verified OI only, shared UI/Dashboard/Watchlist/Scanner/Super Five और errors-only Doctor। B203 phone report को इस workstream के लिए field baseline माना जाएगा।

### 3 — पाँच स्वतंत्र Voting Engines + Canonical Combined Vote (THIRD)
- T/C/N/F/O के individually authenticated source lineage, exact symbol/tf/generation/time/expiry; News/Futures/Options missing evidence `WAIT`, candle-direction overlap और source dependency Doctor।
- Existing `combine_evidence` policy (3 of 5 independent verified eligible; >=2/3 direction agreement and >=10 pp margin) intact। HIST-only replay research vs VERIFIED LIVE vote अलग; कोई broker order या fabricated B/S प्रतिशत नहीं।
- परिणाम सभी स्क्रीन में एकरूप, errors-only full trace; इसके बाद selected-only 5/34/51/70 capacity, 1–4 phone regressions और एक consolidated release gate।

**काम की execution discipline:** हर segment शुरू करने से पहले current हिंदी journal + latest changed files + previous run exact SHA/status/log/artifact; PASS repeat नहीं। Segments के भीतर related tests/fixes combined; हर checkpoint हिंदी issue journal #114 में recorded। Stage 1 को planning/code-staging से शुरू करना अनुमत, लेकिन production server mutation अथवा M LIVE enablement स्वतः नहीं।

---

## एक साझा सत्य
- T Technical, C Candle, N News, F Futures, O Options: पाँच मौजूदा सक्रिय स्लॉट। M Market Brain छठा स्टैंडबाय स्लॉट; अभी शून्य वोट और पाँच-वोट quorum में बदलाव नहीं।
- साझा `combine_evidence`: 3/5 verified independent engines आवश्यक, eligible के कम-से-कम 2/3 का directional agreement, averaged directional margin कम-से-कम 10 percentage points, अन्यथा WAIT। हर असहमत किंतु प्रमाणित वोट शामिल; 4 B/1 S संभावित B, 3 B/2 S WAIT, 4 S/1 B संभावित S, ताकत की शर्त के अधीन।
- 13 technical filters एक ही मूल candle input साझा करते हैं; उन्हें 13 independent engine votes नहीं मानना। 4 options/OI filters context-only को बिना measured authenticated directional flow के LIVE vote नहीं देना। News headlines/RSS sentiment को verified market-impact voting न मानना।
- हर परिणाम के साथ exact symbol, timeframe, provider generation, verified timestamp, source, expiry/contract (जहाँ लागू), status, direction, blocker, adapter version और identity trace जरूरी। Missing या पुराना प्रमाण WAIT, fake percentage निषिद्ध।
- HIST फिल्टर agreement और verified LIVE five-box consensus अलग रखें। Red/green analysis पट्टी बाजार की वास्तविक OHLC candle नहीं है, win probability भी नहीं।

## तीन गणना तथा Doctor
1. Filter Layer: 17 चयनित/18 catalog का वास्तविक calculation या context-only, मूल candle quality और सही timeframe, पूरा नहीं हुआ तो exact blocker।
2. Box Layer: T/C/N/F/O verified independent directional inputs, expiry-specific O and mapped F। हर Box की evidence eligibility, freshness, source और overlap जाँच।
3. Final Layer: एक canonical `combine_evidence` और साझा UI presenter, Dashboard/Watchlist/Scanner/Super Five में consistent data key। सामान्य valid विरोध Error नहीं। Quorum/strength fail हो तो WAIT/NO_CONSENSUS; data poisoning, duplicate source, stale timestamp, provider mismatch, screen display disagreement ही Doctor ERROR-ONLY में दिखें।
- `v3_vote_conflict_doctor.py` नया read-only Conflict Doctor: valid minority और WAIT disagreement non-error, published combined mismatch वास्तविक error। मौजूदा EngineEvidence में independent source-id/lineage उपलब्ध नहीं; overlap की **पूर्ण प्रमाणित जाँच अभी अधूरी** और डॉक्टर को 'UNMEASURED' बताना चाहिए। GUI-pixel प्रमाण अभी नहीं।
- Live data source पर नया verification/broker request Doctor स्वयं नहीं करेगा। Doctor silent when healthy; विस्तृत counts और reasons on demand।

## छठा M Brain: Server-first, ऐप बाद में
**पहले staging में server-side Brain Memory Service**, Oracle Dhan gateway से अलग storage/auth domain/route। Gateway केवल Dhan pipe + token renewal; server पर V3 app preferences/settings नहीं। Market Brain server को LIVE trade/order authority नहीं।
1. Authenticated append-only `prediction_event`, `vote_evidence_reference`, `outcome_event`, `model_policy_version` schemas। Master login से phone 1–4 authorized; encryption, per-user access, signed/idempotent event IDs, retention, revisions, backup और audit log। Secrets or tokens या raw passwords persist नहीं।
2. Staging API अनुबंध (नाम प्रस्तावित, अभी deployed नहीं): POST `/brain/v1/events` (idempotent event write), GET `/brain/v1/sync?since=...`, GET `/brain/v1/health`, GET `/brain/v1/restore` with scoped authorization; no trading endpoint। Device sync outage पर bounded encrypted local pending queue; immutable conflict reconciliation, replay and restore after uninstall/login.
3. Server backup + auth + replay + four-phone conflict tests PASS के बाद V3 ऐप में M slot read-only preview और Brain Sync Doctor। Server न मिले तो M WAIT/STANDBY और T/C/N/F/O पर कोई असर नहीं।
4. 10/15/30/60 minute prediction vs actual outcomes केवल सत्यापित finished window के बाद compare; no lookahead, calibrated research metrics only, no invented prediction % और no runtime self-modifying weights. स्वतंत्र audit और explicit approval के बाद ही छठे vote को activate और 5→6 quorum policy बदलना।
5. Oracle production, V1 और वर्तमान APK पर बिना approved deployment/phone test असर नहीं।

## Release gates
- चरण A (अब): current B202 preview का version/header/artifact/signing PASS, B201 phone failures baseline, कोई नया live claims नहीं।
- चरण B: 4 OI filter diagnostics तथा C/N/F/O real independent sources; developer/unit+cache replay+session tests; NIFTY/BANKNIFTY/SENSEX 1m HIST continuity और scanner vs dashboard parity, 51 selected → max70; Doc errors-only।
- चरण C: B3 exact-source PASS, B196 exact-source PASS, एक संयुक्त अगला Preview APK (नया display/app version और build number साथ)। कोई force-live or disabled sixth vote।
- चरण D: स्वतंत्र Brain server memory staging proof, backup/restore/4-phone, फिर ऐप M module और controlled testing; बाद में audited live activation।
**सभी बदलाव, commands, tests, failures और परिणाम हिंदी जर्नल में दर्ज करें; पुराने PASS अनावश्यक न दोहराएँ।**
