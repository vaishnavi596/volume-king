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
