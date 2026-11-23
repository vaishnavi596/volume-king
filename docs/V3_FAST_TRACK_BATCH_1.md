# BOT KING V3 — संयुक्त FAST TRACK BATCH-1 (ONE BATCH / ONE SOURCE GATE)
**दिनांक:** 23 नवंबर 2026 · **मालिक का निर्देश:** रिपोर्ट देकर न रुकें; एक साथ संबंधित सुधार करें, अगले काम पर बढ़ें।  
**Scope:** V3 `pilot/v1-pure-original-clone-phone-20261120`; V1/V2, Oracle production, Dhan token, वास्तविक orders सुरक्षित।  
**Source checkpoint:** `e18c87f21f2b1acdbd7aa7d27b6190c5d8c63090` — B1/B2/Adapter/B3 offline PASS; B196 safe audit PASS।  
**फोन:** पुरानी B200 रिपोर्ट = पुराने इंस्टॉल किए गए APK की वास्तविक स्थिति; B201 बन जाने पर ही नए checkpoint की फोन पर पुष्टि होगी। B201 workflow #45118044856 अंतिम SUCCESS/FAIL और artifact verification अलग आवश्यक; PENDING को PASS न लिखें।

## एक संयुक्त बैच के पाँच जुड़े हुए वर्कस्ट्रीम
| ID | कार्यक्षेत्र / मूल पाँच सुधार | पुराने फोन की साक्ष्य-स्थिति | मौजूदा कोड / शेष सत्यापन |
|---|---|---|---|
| B1-01 | Dhan quotes, overlap, active-screen priority, bounded refresh/cooldown | 51/51 equity और 3/3 index cached quotes उपलब्ध; exchange/live timestamp unverified | source B1/B2/Adapter PASS; फ़ोन load, 429 वर्गीकरण, SENSEX/WIPRO timestamp, provider pressure बाकी |
| B1-02 | मूल Dhan OHLCV → Oracle normalized → exact-source/timeframe phone history; retention, completed 1m→3m→5m | NIFTY 1m 87 bars; normalized gateway→phone SHA256 match; raw provider UNVERIFIED; 3m selected equities effective 0 while scan 35/54 | `get_market_data` timeframe retention fix e18c87 source PASS; 3m local derivation on-demand and paced warmup; raw OHLCV and post-scan 3m end-to-end बाकी |
| B1-03 | एक साझा HIST/LIVE/WAIT adapter: Dashboard 1m, Watchlist 3m, Scanner selected, Super Five/Chart, Bullish-Bearish + Barrier/Bollinger | HIST T=0/100 (8 directional votes), C=38/62 on 1m; पाँचों verified LIVE WAIT; 5m data not substitute for 1m/3m | Same timeframe+symbol+generation, timestamp, no fabricated LIVE; UI uniformity/last-three-moves/Barrier display real phone acceptance बाकी |
| B1-04 | पाँच स्वतंत्र engines T/C/N/F/O; Scanner 17/18 filters; OI Support/Resistance/Profile, Dhan Max Pain, PCR; sixth inert | 13 technical calculated; 4 options CONTEXT_ONLY/WAIT; headlines cached without verified direction; futures flow missing; five engine verified snapshots 0/5 | independent source proof required; context never live directional vote; exact 1m/3m historical publisher exists, actual UI/phone verification बाकी |
| B1-05 | 5/34/54/70 unique-equity dynamic Smart Data and 1–4 phone stress/performance | selected 51, watchlists 5, duplicate 0, global cap 70, 3 uncached requests/180s, 2s UI tick ≠ upstream request, 3m cached signals 1 | CI bounded/offline tests PASS; real 54/70 end-to-end, 4 phones, background screen-off limitations and scanner completion remaining |

## छठा समापन-गेट — संयुक्त TEST → SIGNED APK → PHONE REPORT → FINAL JOURNAL
- वर्तमान source checkpoint के B1, B2, Adapter, B3, B196 पुराने सफल प्रमाण दोबारा न चलाएँ।
- B201 अलग Android package `com.botking.v3b201.bot_king_v3_b201_preview`, versionCode 201, versionName 2.3.201, disposable isolated signer; B200/V1 पर over-install नहीं।
- B201 #45116797991 FAILED: APK बनाया और explicitly sign हुआ, लेकिन verification ने गलती से 2.3.200 खोजा; upload नहीं हुआ। Version assertion fix `main` commit `218b046e`; B201 #45118044856 RUNNING (audit के समय), result **PENDING**।
- सफल APK तभी घोषित करें जब GitHub job checks FULL TEST + B3 exact SHA + B196 exact SHA + aapt package/label/version + apksigner fingerprint + artifact upload सभी success हों।
- नया Phone Doctor रिपोर्ट आने पर पुराने B200 बनाम नए B201 के प्रति-समस्या comparison से निर्धारित करें: `ALREADY_FIXED_IN_NEW_SOURCE`, `STILL_FAILING_ON_PHONE`, `DATA_PENDING`, `EXPECTED_WAIT`, `NEW_DEFECT`।

## एक ही साझा End-to-End ट्रेस (किसी भी प्रभावित शेयर पर)
`Dhan original OHLCV / quote / option source`
→ `Oracle gateway route, HTTP/error category, provider generation`
→ `phone exact symbol + timeframe (1m/3m/5m) + expiry + timestamp cache`
→ `quality / last-three-move / selected filter calculations`
→ `T/C/N/F/O independent engine/contextual publisher`
→ `Dashboard / Watchlist / Scanner / Super Five / Chart shared display`
→ `HIST | VERIFIED LIVE | WAIT | ERROR Doctor`.

**सच्चाई का नियम:** Cached quotes historical price बता सकते हैं, LIVE नहीं; normalized transport SHA256 ≠ raw Dhan OHLCV proof; HIST analysis ≠ live order-ready signal; OI/PCR/headlines unverified ⇒ CONTEXT_ONLY/WAIT; पाँच इंजन का WAIT अकेले code defect सिद्ध नहीं करता।

## नई फोन रिपोर्ट आते ही चलने वाला एक-पास Fast-Track क्रम
1. **Intake:** APK version/build/source SHA, device & time, NIFTY/BANKNIFTY/SENSEX prices, RELIANCE 1m/3m, Watchlist 51/70, scan completion, filter stages, five engine HIST/LIVE/WAIT, Doctor error HTTP route की उपलब्ध fields read-only लें; कोई डेटा गढ़ें नहीं।
2. **Diff:** इस बैच की पाँच rows से हर complaint मिलाएँ; पुराने source में पहले से PASS fix को दुहराएँ नहीं; 54 compact issues को 54 missing quotes न कहें; 59 FeedError का HTTP कारण अनुमान से 429 न बनाएँ।
3. **One impact map:** वास्तविक defect मिले तो संबंधित provider read/cache/analysis/publisher/UI/tests एक साथ; source/test files के current version देखें; Oracle production/V1 untouched।
4. **One corrective patch:** local syntax/import + impacted positive/negative tests; unmet NOT_EXECUTED लिखें; एक source/test SHA पर स्वतः B3 और प्रासंगिक B1/B2/Adapter + जरूरत पर B196; failed job की exact traceback लेकर उसी बैच का fix करें।
5. **Release:** सभी लागू offline gates exact SHA verified होने पर ही अगला isolated preview APK; physical install, Doctor after scan settled, final VERIFIED/PENDING/FAIL ledger और हिंदी master journal; बग बचा हो तो अगला cycle उसी batch में जारी।
6. **No idle OK loops:** स्वीकृत दायरे में कार्य व जर्नल आगे बढ़ाएँ, सिर्फ बाहरी वास्तविक user action (फोन install/report या GitHub permission) पर ठोस एक निर्देश दें। Running workflow को SUCCESS न बताएं और duplicate builds न चलाएँ।

## वर्तमान open acceptance
- Original raw Dhan→gateway→phone OHLCV parity and exchange timestamp: **OPEN**।
- 3m Watchlist completed history availability after full scan: **OPEN**।
- HIST/LIVE/WAIT consistent five-engine and 17/18 filter UI across screens: **OPEN**।
- Missing 1m/3m independent option/news/futures *verified* evidence: **OPEN**, no fabricated signals।
- 5/34/54/70 dynamic real-device/4-phone benchmarking: **OPEN**।
- B201 install + fresh error report: **AWAITING PHONE REPORT** (APK upload must be verified first)।

**Journal:** `docs/V3_MASTER_JOURNAL.md` is source of truth. This document is the unified execution sheet, not a claim all five workstreams are finished.
