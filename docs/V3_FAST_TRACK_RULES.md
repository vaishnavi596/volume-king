# BOT KING V3 — FAST TRACK 2.0 / ZERO SKIPPED CHECKS
**प्रभावी:** 23 नवंबर 2026  
**Scope:** केवल V3 branch `pilot/v1-pure-original-clone-phone-20261120`; V1, पुरानी V2 और Oracle production अपरिवर्तित।

## अनिवार्य संचालन नियम
1. हर कार्य में पहले `docs/V3_MASTER_JOURNAL.md` और नवीनतम संबंधित बदली फाइलें/वास्तविक CI jobs/logs पढ़ें। पुराने दस commits या पुराने PASS tests को बिना कारण दोबारा न जाँचें।
2. पहले root cause और उससे प्रभावित data→cache→analysis→adapters→UI तथा tests का impact-map बनाएँ। उसी विषय की सभी सुरक्षित fixes एक संयुक्त patch में करें; बिना जाँचे दूसरे modules न बदलें।
3. Push से पहले syntax/import + changed-module targeted positive/negative regression चलाएँ। Targeted PASS *पूर्ण* regression का स्थान नहीं है।
4. एक संयुक्त source SHA पर स्वतः चलने वाला B3 full offline suite अनिवार्य है। B196 manual extra-audit केवल उसके विशिष्ट checks चलाता है; B3 का पूर्ण suite उसी exact SHA पर SUCCESS होना आवश्यक है। बिना दोनों अपेक्षित gates की पुष्टि APK release नहीं।
5. एक ही SHA के verified PASS को reuse करें; failure पर logs में exact failing test, traceback, job और source path जाँचें। केवल rerun या source-text assertion बदलकर वास्तविक defect न छिपाएँ।
6. Docs-only commits Full B3 trigger न करें; source/tests/backend/ops बदलने पर स्वतः B3 full suite और existing concurrency `cancel-in-progress` कायम रहे। Running source patch के दौरान बार-बार छोटे push न करें।
7. HIST, LIVE, WAIT, ERROR और CONTEXT_ONLY स्पष्ट अलग रहें। Exact symbol/timeframe/provider-generation/source/expiry/timestamp तथा 429 rate-limit gates कभी शिथिल न करें। कोई fabricated candle, directional vote, performance या LIVE proof नहीं।
8. API tokens/secrets/logs के संवेदनशील fields कभी journal में न दें। No production Oracle/V1 write, provider fanout, real order या APK creation बिना मौजूदा सुरक्षा तथा user-authorized release flow।
9. GitHub journal में हर approved change: date, baseline SHA, changed files, reason, command/test counts, CI run/job URL, final SUCCESS/FAIL/UNKNOWN, outstanding risks और next step दर्ज हों। Pending को PASS न लिखें।
10. 'OK' = वर्तमान स्वीकृत सुरक्षित scope में आगे बढ़ें। हर छोटे चरण पर confirmation न माँगें। GitHub changes के बाद exact SHA verify करें; कोई workflow trigger न हो तो उसे खुद से PASS न मानें।

## Test ownership / No duplication
- **Targeted:** प्रासंगिक file tests, syntax, missing-data/negative, cross-timeframe contracts; early defect detection.
- **B3 (automatic):** पूर्ण `python -m unittest discover -s tests -v` plus compile/shell validation; mandatory on latest release SHA.
- **B196 (manual):** अतिरिक्त index-429, five/six-box, provider quarantine, session/adapter safety checks. B3 full suite को *दुबारा नहीं* चलाना; एक ही source SHA पर B3 separately confirmed SUCCESS रहे।
- **APK gate:** exact source SHA पर B3 + applicable B196 + other required gates PASS, signing/version identity/Android install/phone tests. CI success != market-live certification.

## Next joint V3 work
Latest OI seven-strike structural window contract का exact-head B3 outcome जाँचें; फिर actual Dhan raw OHLCV vs normalized gateway and phone evidence, independent OI/News/Futures vote eligibility, shared 1m/3m/5m HIST/LIVE UI, 5/34/54/70 four-device stress. पुराने successful fixes duplicate नहीं करने।

## स्थायी Owner Rule: Standalone Max Pain स्थायी रूप से निषिद्ध (23 नवंबर 2026)
- V3 Scanner/Filter Settings/Watchlist/Super Five/Doctor में केवल **Dhan Max Pain** filter और caption मान्य है। स्वतंत्र **Max Pain** नाम से कोई दूसरा filter, slot, series, display caption, scoring या source adapter फिर न जोड़ें।
- पुराने preferences, imported backups या filter modes से standalone label आए तो उसे **एक ही Dhan Max Pain** identity में migrate/dedupe करके valid saved settings में रखें; साथ में अलग legacy filter न बचाएँ। अन्य filters के user choices सुरक्षित रखें।
- Dhan के underlying numeric `max_pain` provider/metrics field, option-chain calculations और audit provenance को न हटाएँ: यही Dhan Max Pain की underlying value है। इसका unverified historical context किसी LIVE/directional vote को authorize नहीं करता।
- Regression का स्थायी contract: registry में `"Max Pain"` अनुपस्थित, `"Dhan Max Pain"` केवल एक; startup, restore और modes migration में duplicate नहीं; सभी UI captions Dhan-qualified; invalid/missing/stale provider evidence ⇒ WAIT।
- उपरोक्त नियम का उल्लंघन regression failure है। Fast Track 2.0 का targeted + exact-SHA B3 Full Gate तथा हिंदी journal नियम लागू रहेंगे।


## Owner rule — संयुक्त सुधार और हर Workflow का अंतिम सत्यापन (23 नवंबर 2026)
- किसी एक मुद्दे के प्रभावित source, backend, adapters, cache, UI और tests की **पूरी impact-list पहले** बनाएँ। सभी संबंधित बदलाव एक नियोजित संयुक्त batch के रूप में लागू करें। बीच-बीच में source-only/test-only micro-push से अनेक अधूरे runs न पैदा करें।
- नवीनतम संबंधित source और हिंदी मास्टर जर्नल पढ़ना अनिवार्य; पुराने दस commits, पुराने PASS या अनावश्यक APK दोहराना निषिद्ध।
- **Push से पहले** स्थानीय/उपलब्ध environment में syntax/import, targeted positive+negative परीक्षण चलाएँ। यदि environment में targeted test चलाना संभव नहीं हुआ, जर्नल में स्पष्ट NOT EXECUTED लिखें; GitHub B3 को उस स्वतंत्र pre-push प्रमाण का विकल्प न बताएं।
- प्रत्येक batch का exact source+test SHA, automatic B3 और जहाँ लागू हो B196/adapter audit का वास्तविक job/traceback/conclusion देखें। Running/pending को PASS न लिखें; FAIL पर उसी बैच का संयुक्त root-cause repair और फिर नए exact-SHA Gate का सत्यापन अनिवार्य।
- पिछला Workflow अभी चल रहा हो तो बिना तत्काल सुरक्षा-कारण नए source Push से उसे अनावश्यक cancel न करें। Docs-only updates must not trigger B3.
- B200 Phone-Test artifact ऐतिहासिक signed checkpoint है; उसके बाद के patches उसमें मौजूद नहीं। नया APK explicit release gate और परीक्षण-उद्देश्य पर ही, Oracle/V1/V2 सुरक्षित।
- हर result—PASS, FAIL, CANCELLED, PENDING, NOT EXECUTED—को उसी रूप में हिंदी मास्टर जर्नल में दर्ज करें; अगली कार्रवाई तभी चुनें।


## 25 नवंबर 2026 — OWNER APPROVED: SMART 3.0 TURBO COMPACT (अनिवार्य)
यह वर्तमान कार्यप्रणाली SMART 2.0 को supersede करती है; पुराने सुरक्षा, सत्यापन और source-isolation नियम बरकरार हैं।
पाँच चरण: REVERSE SCAN → JOINT FIX → JOINT TEST → AUTO CONTINUE → FINAL CLOSE.
सात नियम: ZERO SKIP, ZERO INCOMPLETE, ZERO DUPLICATE, ZERO IDLE (उपलब्ध सक्रिय सत्र में), MAXIMUM JOINT WORK, MINIMUM CI COST, MINIMUM TALK.
**STRICT DEPENDENCY CLOSURE / NO BYPASS:** जिस कार्यसमूह को शुरू किया है, उसके सभी आवश्यक dependencies (app, server/gateway, Dhan source, owner phone/install/permissions/report, wiring, tests, evidence) का वास्तविक समापन और verification किए बिना आगे का dependent कार्य या अगला मुख्य Batch शुरू नहीं होगा। प्रत्येक dependency को owner/AI/server, exact action, evidence और PASS/FAIL/BLOCKED/PENDING से register करें। Owner/server action जरूरी हो तो एक बार स्पष्ट, संक्षिप्त निर्देश दें; उसी gate पर BLOCKED रखें; समाधान का प्रमाण जाँचकर ही खोलें। बिना अनुमति server production, credentials या real orders न बदलें। BLOCKED को PASS, skip या defer करके batch बंद न करें।
एक सुरक्षित संयुक्त source+test+journal commit; fail-fast targeted tests फिर आवश्यक exact-SHA full gate; Workflow चलते समय केवल non-conflicting read-only तैयारी, नया competing push नहीं। वास्तविक logs और फोन evidence से closure; छह मूल ML5 Batch ही रखें। प्रत्येक batch की सभी acceptance rows PASS तभी CLOSED; अन्यथा OPEN/BLOCKED। बार-बार OK नहीं; सिर्फ आवश्यक user action, unresolved blocker या completed batch की compact report। Chat session के बाहर autonomous AI coding उपलब्ध मानकर न चलें। GitHub automated controller अभी प्रस्तावित, implementation अलग सत्यापन के अधीन।
