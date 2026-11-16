# BOT KING — पिछले दो कार्य-चैट का क्रमवार प्रमाण-आधारित ऑडिट

**कवरेज:** 14–15 नवंबर 2026 के उपलब्ध दो पूर्ववर्ती BOT KING कार्य-चैट, उनमें उद्धृत Android screenshots/Oracle logs, और GitHub में सुरक्षित समकालीन ऑडिट। वर्तमान चैट के अतिरिक्त S17–S19 प्रमाण अलग परिशिष्ट में हैं।

**महत्वपूर्ण सीमा:** यह *उपलब्ध* चैट इतिहास, पूर्व रिपोर्ट और GitHub से पुनः पढ़े परिणामों का संकलन है; दोनों चैट के हर संदेश/हर Terminal Command का पूर्ण निर्यात उपलब्ध नहीं था। जहाँ सटीक मूल command/output नहीं मिला, उसे दोबारा बनाकर सत्यापित तथ्य की तरह प्रस्तुत नहीं किया गया है।

**मुख्य Source-of-Truth:** `BOT_KING_HANDOFF.md`, `docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md`, `docs/botking-mobile-audit-batches-20261115.md`, `docs/B3_GITHUB_FULL_AUDIT_20261115.md`, और GitHub Actions के दिए गए लिंक। पुरानी तारीख का दस्तावेज़ नई deployment स्थिति का प्रमाण नहीं है।

### प्रमाण के प्रकार
- **[U]** = पिछले चैट में उपयोगकर्ता द्वारा भेजा terminal output या मोबाइल अवलोकन; जो विवरण नहीं दिखे उन्हें नहीं गढ़ा गया।
- **[G]** = GitHub commit/workflow या repo में सुरक्षित कार्य-रिपोर्ट से पुष्टि।
- **[A]** = पुराने सहायक का काम-सारांश; स्वतंत्र परीक्षण का दर्ज प्रमाण नहीं।
- **[P]** = केवल योजना/बकाया, PASS नहीं।
- **[C]** = वर्तमान चैट में दोबारा साझा किया गया नया प्रमाण; पहले दो चैटों से अलग।

## चैट 1 — 14 नवंबर: Scanner, Candle, Index और APK Recovery

01. **[U] Index mapping शुरुआती स्थिति:** NIFTY mapping PASS, BANKNIFTY/SENSEX FAIL बताए गए। एक अनधिकृत `/dhan/status` probe पर 403 आया; इससे OAuth खराब होने की पुष्टि नहीं होती।
02. **[U] Server safety:** `/health` HTTP 200, `broker_connected:false`, `live_orders_enabled:false`; Python compile exit 0। सेवा 14 नवंबर की बाद की जाँच में active थी।
03. **[U] Production access सीमा:** `/etc/bot-king` root-only directory; `opc` के लिए सीधे access नहीं। यह permission-design था, आवश्यक रूप से backend outage नहीं।
04. **[U] Auth material access:** पुराने readonly test में local health 200 और अलग pairing-key file accessible रिपोर्ट हुई। Key contents किसी GitHub रिकॉर्ड में न डालें।
05. **[U] Watchlist/Index mismatch:** उपयोगकर्ता ने equity watchlist quotes आते देखे, जबकि NIFTY/BANKNIFTY/SENSEX में lag/availability समस्या थी। Index को 51-equity batch के पीछे नहीं रोकने का निर्णय।
06. **[U] Candle coverage:** कुछ प्रतीकों पर candles दिखीं, शेष में missing/partial। Candle History की सफलता को exchange-live price का प्रमाण नहीं माना गया।
07. **[U] Scanner page:** Scanner पेज न खुलना और नीचे Bullish/Bearish filter-result न दिखना उपयोगकर्ता ने बताया; उसी क्षेत्र के screenshots भेजे।
08. **[A/G] Scanner hardening:** navigation recovery, independent widget-error isolation, cached-analysis KeyError protection तथा regression additions पुराने चैट के कार्य-सारांश में दर्ज हैं। हर intermediate patch को device PASS नहीं मानें।
09. **[G] v2.3.110 APK:** Workflow [43633395284](https://github.com/vaishnavi596/volume-king/actions/runs/43633395284) पुराने सारांश में SUCCESS; 666 offline tests और signing/artifact PASS दर्ज।
10. **[U] v2.3.110 mobile:** उस version पर 51/51 LTP और 51 candle analyses के observations मिले; live signals unavailable, five engines 0/5 independently verified; कुछ HTTPError/FeedError भी दर्ज। Mobile 10-filter test अभी अलग रह गया।
11. **[G] Candle regression workflow:** [43590671041](https://github.com/vaishnavi596/volume-king/actions/runs/43590671041) commit `1648116` FAILED; यह पुराने intermediate build का परिणाम था, पूरे भविष्य के branch का नहीं।
12. **[G] Other intermediate failures:** 14 नवंबर के `b2d1765` और `6d1eee4` offline regressions FAILED report हुए। हर Fail के लिए log/commit आधारित root cause आवश्यक; commit success की मान्यता नहीं।
13. **[U/A] User workflow constraint:** 2–4 संबंधित fixes एक batch में, पहले पुराने batches का audit, फिर नया APK; बिना जरूरत फोटो न बनाना; repetitive “ok” confirmations की बजाय कार्रवाई।

## चैट 2 — 15 नवंबर: Joint Audit, Dhan Registry, Options, Paper Bot और Oracle

14. **[U] v2.3.113 Android findings:** Pairing header `UnicodeEncodeError`, equity-watchlist `FeedError`, chart सफेद होना, BANKNIFTY/SENSEX intermittently unavailable; डेटा की freshness अभी unverified।
15. **[G] Pairing guard:** non-ASCII header rejection और sanitized error handling `test_dhan_pairing_ascii.py` के साथ audit में दर्ज। Pairing key rotate करने का निर्देश नहीं।
16. **[G] Watchlist refresh:** shared 60s equity snapshot timer, last-good quotes retention, sanitized Oracle snapshot errors के tests। Android वास्तव में rates दिखा रहा था या नहीं—अलग acceptance।
17. **[U] Chart blank reproducibility:** Scanner में NIFTY से अन्य symbol पर change करने पर white WebView; page छोड़कर वापस आने से candles दिख सकती थीं।
18. **[G] Chart recovery commits:** `2487368` और `49bcdd3`; current-symbol saved OHLC को retry, cross-symbol candle contamination या duplicate upstream fanout न हो। Mobile PASS बाक़ी।
19. **[U] v2.3.114 health:** `54-symbol filters • 51 analyzed • 3 errors`; HDFCBANK, HINDUNILVR, NTPC failures; `scanner: FeedError` दिखा, पर precise upstream HTTP code सिद्ध नहीं था।
20. **[U] Recovered error semantics:** `dhan_index_ltp_batch: FeedError` RECOVERED भी देखा गया। Historical `HIST • NOT live` अपने आप failure नहीं।
21. **[U] Close-market behavior:** अंतिम उपलब्ध Rates Dashboard/Watchlist/Super Five में Login पर एक बार लाना; उसके बाद बंद बाजार में repeated requests रोकना; अगला कारोबारी सत्र खुले तो नियमित refresh।
22. **[G/P] Market-session checkpoint:** Commits `54c3ab3`, `321ea2c`, `b614ab1` और पुराने assertions adjustments; regression [43682835716](https://github.com/vaishnavi596/volume-king/actions/runs/43682835716) को समकालीन रिपोर्ट PASS कहती है। Official NSE/BSE special-session holiday calendar अभी पूर्ण नहीं।
23. **[G] Central filter editor:** 10/10 saved active slots; remove/add पर available filters और OI Context वापस; commits `de624e6`, `3b2fcf9`, tests `e010116`, `f2b22d3`; unverified OI vote WAIT ही रहेगा।
24. **[G] v2.3.121:** Build [43701787694](https://github.com/vaishnavi596/volume-king/actions/runs/43701787694) पर previous audit में 751 tests, signing PASS, `versionName=2.3.121`, `versionCode=73601` दर्ज। यह newer v2.3.125 का device PASS नहीं।
25. **[U] v2.3.121 Options screenshots:** NIFTY के एक listed expiry का seven-strike CE window दिखा; ICICIBANK expiry/HTTP 422 error। Mapping/entitlement/which route failed का निष्कर्ष screenshot से नहीं निकलता।
26. **[G] Options negative cache:** per-symbol/expiry 422 handling और avoiding rapid repeat requests audit में बताया गया। News/Futures/Options independent directional signals पर्याप्त verified नहीं; falsely 5/5 न बताएं।
27. **[U] Oracle S05-B:** Registry 2,785 records; selected API regression reported PASS; staging only; provider requests 0, production changed NO।
28. **[U] Earlier S05 source-state warning:** एक जांच में `watchlist_api.py` / `watchlist_store.py` absent और `S05_CODE_INTEGRATED: False` रिपोर्ट; later S12–S18 ने इन्हें मौजूद बताया। **यह अलग समय की snapshots हैं; पुराने snapshot को वर्तमान state न मानें।**
29. **[U] Oracle S06 staging:** five-direction, invalid-data rejection, signal-safety tests PASS; production changed NO और provider requests 0।
30. **[U] Futures/News audit gap:** Future OI/money flow, sourced News sentiment और स्वतंत्र live directional score routes नहीं दिखे; सिर्फ display का होना signal source verified होने का प्रमाण नहीं।
31. **[U] Instrument master check:** TMCV के BSE/NSE equity records देखे गए; futures/options listing का प्रमाण नहीं।
32. **[U] Backup warning:** एक समय `server.py` backup मौजूद, `dhan_feed.py` का अपेक्षित timestamp backup missing; बाद के assistant summary में “both PASS” कहा गया था—उस assertion को independent PASS न लिखें।
33. **[A/G] Joint branch:** `fix/botking-joint-audit-70-15-20261115`; commits `e8d2e777`, `aa6e44b0`, `e6d6926b` और 776→778 tests PASS का पुराने chat summary में उल्लेख।
34. **[G] Registry Android/Oracle parity:** GitHub `cb18300a` registry loader, `a1ed56db` search, `83749508` selected-LTP batch, `94dfa56c` actual Oracle registry-search response shape, `d06e9b3a` S14 stage, `73378bf0` tests fix। Last `73378bf0` offline suite 792 PASS; Oracle state अलग जाँच जरूरी।
35. **[U] S12 audit:** Oracle service active, health 200, live orders disabled; 2,785 NSE registry records and 5-watchlist route integration; `server.py` में Oracle-specific Assessment/OI/expiry cache संरक्षित रखना आवश्यक।
36. **[U] S14 source inspection:** Existing `/v2/instruments/search` already registered in `watchlist_api.py`. Duplicate route add नहीं। Legacy equity LTP snapshot अलग, selected equity batch नया।
37. **[U] S15 proposed file:** `server.s14.proposed.20261115T174909Z.py`; syntactic PASS, 2 option guards and 1 selected-LTP route; staging alone deployment नहीं।
38. **[U] S15 production deploy:** Hash+backup verification PASS, service restart और health PASS, rollback required NO, live orders settings unchanged, orders 0। **यह Oracle server.py route patch के deployment का प्रमाण है।**
39. **[U] S16 static audit:** syntax PASS; selected batch route count 1, dynamic option mapping count 2; production changed NO **during that check**।
40. **[U] S17 authenticated vs unauthenticated distinction:** 13/13 security/health PASS; protected routes 403 without key; provider requests 0। यह authenticated market functionality का परीक्षण नहीं।
41. **[U] S18 WatchlistStore source:** `count=5, limit=70` per list; `validate()` duplicates एक सूची के अंदर रोकता; `replace()` atomic save/rollback। 70 total तथा cross-list duplicate रोकने का server code **उस समय अभी मौजूद नहीं**।
42. **[G] Joint watchlist fix:** Android one-symbol-one-list और global 70, Oracle `scripts/oracle_s18_watchlist_patch.py` staged script; `c89368fd`, offline 797/797 PASS। Oracle S18 patch deployed का प्रमाण उपलब्ध नहीं।
43. **[G] Master contract + release workflow:** `70ba1475` contract saved; `683ec5c4` संयुक्त branch को APK workflow में शामिल किया; 799/799 offline tests PASS।
44. **[A/G] Paper Bot:** 5 local simulated bot slots और paper-only engine; existing multiple paper ledgers/market timestamp limitations; no verified live orders. Branch version 2.3.123, older main version अलग।

## वर्तमान चैट का अलग परिशिष्ट — नए प्रमाण, पुराने चैट में न मिलाएँ

45. **[C] Emergency Oracle:** service active, health 200, authenticated market-data server independent: initial no-key GET checks showed 403 and GET index batch 405 (POST-only); no sampled Traceback/NameError/429 in provided journal window।
46. **[C] Authenticated S19-related tests:** `GET /dhan/status` HTTP 200 authenticated true, token oauth_consent/expiry_checked, no reauth; `GET /v2/snapshot` HTTP 200 with 51 equity quotes, snapshot age 79.1 seconds, freshness unverified।
47. **[C] Index POST:** `/dhan/index-ltp-batch` HTTP 200: NIFTY 25144.3 / BANKNIFTY 61034.1 / SENSEX 81592.45, unavailable=[]। ये **test-time last known** prices हैं; current exchange live का दावा नहीं।
48. **[G] 2.3.124:** source release `43a3bcc4`, signed APK build [43746262145](https://github.com/vaishnavi596/volume-king/actions/runs/43746262145) SUCCESS; installed APK acceptance unverified।
49. **[G] Android first-login recovery:** `4e50d226` individual NIFTY LTP failure (other than 429) पर independently validated index batch fallback; `6bf04e96` and `ea22fb2e` intermediate regression FAIL; corrected `ee1d75a4` = 804/804 PASS।
50. **[G] 2.3.125 final build check:** `e587485b`; APK build [43751755544](https://github.com/vaishnavi596/volume-king/actions/runs/43751755544) **SUCCESS**, 804 offline tests PASS; `versionName=2.3.125`, `versionCode=74001`, permanent signing verification PASS, artifact `volume-king-apk` ID `14175849838` uploaded। **Phone install/on-device functional PASS अभी उपलब्ध नहीं**।
51. **[G] Current handoff:** `61ef08c1` root `BOT_KING_HANDOFF.md` and continuous journal introduced. This historical audit is a separate later document, not a re-write of user outputs।

## दो चैट से निकले नियम — आने वाले काम में न भूलें

1. Oracle के चल रहे `server.py` को GitHub `backend/server.py` से wholesale replace न करें; backup + exact hashes + syntax + health + rollback हर production change पर।
2. Dhan-only read-only data और simulated Paper Bot; live orders OFF; किसी real trade का आदेश नहीं।
3. UI में last-good quote retention, लेकिन cache को LIVE नहीं कहना; trading calendar unknown/special sessions conservative।
4. Watchlist **पाँच सूचियाँ, कुल 70 stocks, एक symbol एक ही सूची**। Oracle server-side S18 patch final deploy still pending।
5. Index batch independent; watchlist snapshot independent; Super Five uses existing verified-source cache, scanner candles slow/paced; no request fanout.
6. 429 पर provider cooldown; no repeated requests, no token rotation; no silent Yahoo/Angel fallback.
7. Build success / offline PASS / Oracle deployed / authenticated Dhan verified / installed APK / Android smoke **छह अलग status**।
8. नई चैट: root `BOT_KING_HANDOFF.md` और यह report पढ़ें, latest branch HEAD, last Actions run, and installed app version compare; user से वही server audit फिर-फिर न कराएँ।
9. प्रत्येक batch के बाद `docs/BOT_KING_WORK_LOG.md` में evidence-backed entry commit करें।
10. अधूरे फ़िल्टर/News/Futures/Options data पर directional percentage गढ़कर न दिखाएँ।

## उपलब्ध नहीं या अभी अधूरा

- दोनों पुराने चैटों के **हर shell command, हर timestamped full output, सभी screenshots की original bytes और सभी intermediate CI logs** एक साथ उपलब्ध नहीं थे; यह 100% transcript dump नहीं।
- कई पुराने assistant PASS summaries की exact source run/result reread नहीं हुई; वे ऊपर [A] या समकालीन लिखित audit-based [G] के साथ सीमित हैं।
- कौन-सा APK वर्तमान में उपयोगकर्ता के फोन पर स्थापित है—अप्रमाणित।
- v2.3.125 की screen-level, data-display और next-open-session 09:15+ की mobile verification अभी pending।
- Oracle global-70 WatchlistStore patch के successful deployment का प्रमाण नहीं।
- News/Futures/Options पूर्ण स्वतंत्र verified scoring और official special-session calendar अपूर्ण/अप्रमाणित।


## 2026-11-16 — Historical audit parity addendum (no retroactive PASS)

- This report's bounded **Nov 14–15** historical audit remains intact. Its old release/status checkpoints must be read as dated snapshots; they are not a claim that today's v2.3.128 build or Oracle production is healthy.
- Cross-compared its ten cross-chat rules with `BOT_KING_HANDOFF.md`, canonical master checklist, and the subsequent Nov 16 `docs/BOT_KING_WORK_LOG.md` entries. Earlier six-batch app, S15/S18 Oracle deployment gates, 70 globally unique cross-list watchlist rule, source-vs-CI-vs-device distinctions, and failure/cooldown rules are **already recorded**. No unsupported retroactive completion was marked.
- Newly missing continuation is now explicitly linked rather than inserted into Nov 14–15 chronology: new four-pipeline **DISCUSSION/PROPOSAL**, 20 refresh-demand inventory, no-repeat Oracle evidence commands/sha dry-run, v2.3.127 actual mobile seven-error failure and user-reported v2.3.128 build FAIL. See `BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md`, `BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md`, and latest Work Log.
- Remaining gap: a 100% transcript-level reconciliation of **every** prior shell command, timestamped full output, intermediate CI job and screenshot is impossible from the accessible historical summaries; preserve this limit instead of inventing a command result. For each newly supplied owner output, append a specific entry and link the runbook, instead of asking to redo proven checks.
