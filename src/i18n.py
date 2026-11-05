"""Offline UI translation. Market symbols, provider keys and entered values stay unchanged."""
import re
HI={
"My BOT KING server HTTPS address (optional)":"अपने BOT KING सर्वर का HTTPS पता (वैकल्पिक)",
"Server access key (not saved)":"सर्वर की एक्सेस की (सेव नहीं होगी)",
"I trust this server to receive my Angel One login":"मैं अपना Angel One लॉगिन इस भरोसेमंद सर्वर को भेजने के लिए सहमत हूँ",
"Confirm that you trust this server before sending your broker login.":"ब्रोकर लॉगिन भेजने से पहले पुष्टि करें कि यह आपका भरोसेमंद सर्वर है।",
"Home":"होम","Options":"ऑप्शन्स","Settings":"सेटिंग्स","Scanner":"स्कैनर",
"Settings & Trading Bot":"सेटिंग्स और ट्रेडिंग बॉट","Options • One scroll page":"ऑप्शन्स • एक स्क्रॉल पेज",
"RULE-BASED SCANNER • Chart & Analysis":"नियम आधारित स्कैनर • चार्ट और विश्लेषण",
"Market data mode":"डेटा का स्रोत चुनें","DATA SOURCE":"डेटा स्रोत","Data provider":"डेटा प्रदाता",
"Save changes":"बदलाव सेव करें","Add":"जोड़ें","Remove":"हटाएँ","Hide":"छिपाएँ","Show":"दिखाएँ",
"Add symbol":"सिंबल जोड़ें","Select filter":"फ़िल्टर चुनें","Find indicator":"इंडिकेटर खोजें",
"Restore default 10":"डिफॉल्ट 10 फ़िल्टर वापस लाएँ","Refresh history now":"इतिहास दोबारा लाएँ",
"Refresh selected data":"चुना हुआ डेटा रीफ्रेश करें","Retry chart":"चार्ट दोबारा खोलें","Open in browser":"ब्राउज़र में खोलें",
"Load option premium chart":"ऑप्शन प्रीमियम चार्ट खोलें","Trading mode":"ट्रेडिंग मोड",
"Broker & Data Source":"ब्रोकर और डेटा स्रोत","Select Indian API broker":"भारतीय API ब्रोकर चुनें",
"Connect / Check":"कनेक्ट / जाँच करें","Clear / Disconnect":"साफ करें / डिस्कनेक्ट",
"Index / Stock":"इंडेक्स / शेयर","Instrument":"इंस्ट्रूमेंट","Contract":"कॉन्ट्रैक्ट",
"Expiry":"एक्सपायरी","Expiry selection":"एक्सपायरी चुनें","Expiry date (calendar preview)":"एक्सपायरी तारीख (कैलेंडर अनुमान)",
"Expiry (YYYY-MM-DD)":"एक्सपायरी (वर्ष-महीना-दिन)","Number of lots":"लॉट की संख्या","Lots (paper)":"लॉट (पेपर)",
"Strike":"स्ट्राइक","STRIKE":"स्ट्राइक","Strike price":"स्ट्राइक भाव","Option type":"ऑप्शन का प्रकार",
"Option Chain":"ऑप्शन चेन","Option Chart":"ऑप्शन चार्ट","OI Analysis":"ओपन इंटरेस्ट विश्लेषण",
"Put Call Ratio":"पुट-कॉल अनुपात","Strategy Selector":"रणनीति चुनें",
"CE Premium":"कॉल प्रीमियम","PE Premium":"पुट प्रीमियम","CE OI":"कॉल OI","PE OI":"पुट OI",
"CALL (CE)":"कॉल (CE)","PUT (PE)":"पुट (PE)","BUY • Paper":"खरीदें • पेपर","SELL • Paper":"बेचें • पेपर",
"BUY (Paper)":"खरीदें (पेपर)","SELL (Paper)":"बेचें (पेपर)","EXIT":"बाहर निकलें",
"Stop loss %":"स्टॉप लॉस %","Target %":"लक्ष्य %","Max trades per day":"एक दिन में अधिकतम ट्रेड",
"Entry premium (INR)":"एंट्री प्रीमियम (₹)","Units per lot (verify with exchange)":"प्रति लॉट यूनिट (एक्सचेंज से जाँचें)",
"Premium budget":"प्रीमियम बजट","Historical period":"इतिहास की अवधि","Candle timeframe":"कैंडल की अवधि",
"Market / NSE stock":"बाजार / NSE शेयर","Chart display":"चार्ट का प्रकार","Chart provider":"चार्ट दिखाने का तरीका",
"Auto refresh interval":"ऑटो रीफ्रेश अंतराल","Auto Scan (while app is open)":"ऑटो स्कैन (ऐप खुला रहने पर)",
"Custom minimum (₹)":"अपना न्यूनतम (₹)","Custom maximum (₹)":"अपना अधिकतम (₹)",
"Custom symbol (optional)":"अपना सिंबल (वैकल्पिक)","Custom HTTPS API endpoint":"अपना HTTPS API पता",
"Illustrative days to expiry (NOT actual NSE expiry)":"उदाहरण में एक्सपायरी तक दिन (वास्तविक NSE एक्सपायरी नहीं)",
"Auto entry (saved plan only)":"ऑटो एंट्री (केवल सेव किया प्लान)","Re-entry after exit (saved plan)":"निकास के बाद दोबारा एंट्री (प्लान)",
"Buy on dip (saved plan only)":"गिरावट पर खरीद (केवल प्लान)","Partial profit booking (plan)":"आंशिक मुनाफा बुकिंग (प्लान)",
"Trailing stop (calculation only)":"ट्रेलिंग स्टॉप (केवल गणना)","Maximum total lots":"कुल अधिकतम लॉट",
"Minimum dip before adding (%)":"और जोड़ने से पहले न्यूनतम गिरावट (%)","Re-entry cooldown (minutes)":"दोबारा एंट्री से पहले विराम (मिनट)",
"Daily planned-risk budget (paper INR)":"दैनिक नियोजित जोखिम बजट (पेपर ₹)","Paper square-off time":"पेपर ट्रेड बंद करने का समय",
"Emergency stop (paper)":"आपात रोक (पेपर)","CALCULATE PLAN":"प्लान की गणना करें",
"POSITION PROTECTION • PAPER DEMONSTRATION":"पोजीशन सुरक्षा • पेपर प्रदर्शन","Position protection • PAPER ONLY":"पोजीशन सुरक्षा • केवल पेपर",
"Enable paper protection demonstration":"पेपर सुरक्षा प्रदर्शन चालू करें",
"Paper alert / exit loss (INR)":"पेपर नुकसान अलर्ट / निकास सीमा (₹)","Paper profit target (INR)":"पेपर लाभ लक्ष्य (₹)",
"Profit giveback from peak (%)":"ऊपरी लाभ से वापस गिरने की सीमा (%)","Assisted response timeout (seconds)":"जवाब का इंतजार (सेकंड)",
"Allow PAPER exit after timeout if I do not respond":"जवाब न देने पर समय पूरा होने पर पेपर निकास की अनुमति",
"Current PAPER premium • manually supplied":"वर्तमान पेपर प्रीमियम • मैन्युअल",
"Check PAPER position":"पेपर पोजीशन जाँचें","Confirm PAPER exit":"पेपर निकास की पुष्टि",
"BACKUP / RESTORE":"बैकअप / वापस लाएँ","Prepare backup":"बैकअप बनाएँ","Copy backup":"बैकअप कॉपी करें",
"Restore normal settings":"सामान्य सेटिंग्स वापस लाएँ","Undo last setting change":"पिछला सेटिंग बदलाव वापस लें",
"Backup JSON • copy/export or paste to restore":"बैकअप JSON • कॉपी करें या वापस लाने के लिए पेस्ट करें",
"Replace normal settings from this backup; automatic actions stay OFF":"इस बैकअप की सामान्य सेटिंग्स लगाएँ; ऑटो क्रियाएँ बंद रहेंगी",
"SETTING CHANGE HISTORY":"सेटिंग बदलाव का इतिहास","PAPER TRADE JOURNAL":"पेपर ट्रेड रिकॉर्ड",
"MARKET & DATA STATUS":"बाजार और डेटा स्थिति","MARKET OVERVIEW":"बाजार का अवलोकन","API STATUS":"API की स्थिति",
"NEWS & EVENT CONTEXT":"खबरें और घटनाएँ","TODAY'S PAPER RISK":"आज का पेपर जोखिम",
"My Positions • Paper Only":"मेरी पोजीशन • केवल पेपर","Recent paper orders":"हाल के पेपर ऑर्डर",
"10 DEFAULT ANALYSIS FILTERS • ON/OFF":"10 डिफॉल्ट विश्लेषण फ़िल्टर • चालू/बंद",
"ADD EXTRA FILTERS • Saved":"अतिरिक्त फ़िल्टर जोड़ें • सेव","SUPER FIVE • CANDLE CANDIDATES + COMBINED CHECK":"सुपर फाइव • कैंडल चयन और संयुक्त जाँच",
"Premium Money Flow • Volume activity only":"प्रीमियम फ्लो • केवल वॉल्यूम गतिविधि",
"01  TRADING MODE":"01  ट्रेडिंग मोड","02  OPTION CONTRACT":"02  ऑप्शन कॉन्ट्रैक्ट",
"03  RISK & TARGET":"03  जोखिम और लक्ष्य","04  AUTO STRATEGY (PREFERENCES ONLY)":"04  ऑटो रणनीति (केवल प्राथमिकताएँ)",
"05  PAPER TRADE CONTROLS":"05  पेपर ट्रेड नियंत्रण","06  SIGNAL FILTER":"06  संकेत फ़िल्टर",
"07  ALERTS • NOT CONNECTED":"07  अलर्ट • कनेक्ट नहीं","08  BACKTEST • NOT CONNECTED":"08  बैकटेस्ट • कनेक्ट नहीं",
"09  DIAGNOSTICS":"09  त्रुटि जाँच","No open paper positions":"कोई खुली पेपर पोजीशन नहीं",
"No errors recorded this session":"इस सत्र में कोई त्रुटि दर्ज नहीं",
"No option quote timestamps yet":"अभी ऑप्शन भाव का समय नहीं मिला",
"No recorded entries/exits in this journal yet.":"इस रिकॉर्ड में अभी एंट्री/निकास नहीं है।",
"Selected strategy: None":"चुनी रणनीति: कोई नहीं","Saved paper position: FLAT":"सेव पेपर पोजीशन: कोई खुली नहीं",
"Emergency stop: OFF":"आपात रोक: बंद","Awaiting automatic scan":"ऑटो स्कैन का इंतजार",
"Auto Scan OFF • saved preference":"ऑटो स्कैन बंद • सेव प्राथमिकता",
"Outside regular session hours • automatic refresh paused":"नियमित बाजार समय के बाहर • ऑटो रीफ्रेश रुका है",
"No data • quote time unavailable":"डेटा नहीं • भाव का समय उपलब्ध नहीं",
"Connecting Yahoo Finance…":"Yahoo Finance कनेक्ट हो रहा है…","Use for":"इस्तेमाल करें",
"Use for • chart overlay not implemented":"इस्तेमाल करें • चार्ट ओवरले अभी नहीं बना",
"Minimum directional vote agreement — not success probability":"दिशा बताने वाले फ़िल्टर का न्यूनतम मेल — सफलता की संभावना नहीं",
"Enter contract and tap Calculate.":"कॉन्ट्रैक्ट भरें और गणना दबाएँ।",
"All settings below • changes save automatically • credentials are not saved":"नीचे की सामान्य सेटिंग्स अपने आप सेव होती हैं • निजी credentials सेव नहीं होते",
"Calendar estimate only; holidays and listed contracts need broker/exchange verification.":"केवल कैलेंडर अनुमान; छुट्टियाँ और सूचीबद्ध कॉन्ट्रैक्ट ब्रोकर/एक्सचेंज से जाँचें।",
"Calendar estimate only. Holiday shifts and exchange-listed expiries are not verified; paper mode only.":"केवल कैलेंडर अनुमान; छुट्टी के बदलाव और एक्सपायरी सत्यापित नहीं हैं। केवल पेपर मोड।",
"Option paper entry requires verified premium and lot size.":"ऑप्शन पेपर एंट्री के लिए सही प्रीमियम और लॉट आकार चाहिए।",
"Table uses listed broker contracts when connected. The strike input below is a manual selection; paper orders remain manual.":"कनेक्शन पर तालिका ब्रोकर के सूचीबद्ध कॉन्ट्रैक्ट दिखाती है। नीचे की स्ट्राइक मैन्युअल है; पेपर ऑर्डर मैन्युअल हैं।",
"Underlying prices use the selected data source; Yahoo history may be delayed.":"मूल शेयर/इंडेक्स के भाव चुने स्रोत से आते हैं; Yahoo इतिहास में देरी हो सकती है।",
"Connect Angel One for verified CE/PE quotes. Yahoo supplies underlying data only.":"सत्यापित कॉल/पुट भाव के लिए Angel One जोड़ें। Yahoo यहाँ मूल शेयर/इंडेक्स का डेटा देता है।",
"Verified option-chain feed not connected; CE/PE premiums and OI are unavailable.":"सत्यापित ऑप्शन चेन जुड़ी नहीं; कॉल/पुट प्रीमियम और OI उपलब्ध नहीं हैं।",
"Verified option quotes unavailable; underlying data may still be available.":"सत्यापित ऑप्शन भाव उपलब्ध नहीं; मूल शेयर/इंडेक्स डेटा मिल सकता है।",
"Yahoo adapter has no verified NSE option premium history; Angel One connection and listed contract required.":"Yahoo कनेक्शन में सत्यापित NSE ऑप्शन प्रीमियम इतिहास नहीं है; Angel One और सूचीबद्ध कॉन्ट्रैक्ट चाहिए।",
"These control background scanner votes and Top 5 ranking, not chart visibility.":"ये स्कैनर के फ़िल्टर वोट और टॉप फाइव क्रम नियंत्रित करते हैं, चार्ट पर दिखना नहीं।",
"Unavailable data cannot vote. Adding a filter does not imply a plotted overlay.":"डेटा न मिलने पर फ़िल्टर वोट नहीं देता। फ़िल्टर जोड़ने से चार्ट पर उसकी रेखा बनना जरूरी नहीं।",
"Additional indicators: choose below; OI/PCR require verified exchange data.":"अतिरिक्त इंडिकेटर नीचे चुनें; OI/PCR के लिए सत्यापित डेटा चाहिए।",
"No extra filters added. Add below; each extra filter will appear here.":"अभी अतिरिक्त फ़िल्टर नहीं है। नीचे जोड़ें; हर अतिरिक्त फ़िल्टर यहाँ दिखेगा।",
"Educational preview only; no orders are placed":"केवल समझने का उदाहरण; असली ऑर्डर नहीं जाते",
"Paper simulation only. Manual, Semi-Auto and Auto do not place real orders.":"केवल पेपर अभ्यास। Manual, Semi-Auto और Auto असली ऑर्डर नहीं भेजते।",
"Live broker orders are not connected. Strategy switches save plans only.":"असली ब्रोकर ऑर्डर जुड़े नहीं हैं। रणनीति स्विच केवल प्लान सेव करते हैं।",
"Paper orders use manually entered premium, not live market prices. SL/target are displayed, not executed.":"पेपर ऑर्डर मैन्युअल प्रीमियम से चलते हैं। SL/लक्ष्य केवल दिखते हैं, अपने आप लागू नहीं होते।",
"Trailing stop is a saved preference only. It does not automatically update or execute orders.":"ट्रेलिंग स्टॉप केवल सेव प्राथमिकता है; यह ऑर्डर अपने आप अपडेट या execute नहीं करता।",
"Paper calculator uses manual premium and lot size. Connected broker quotes are shown on Options.":"पेपर गणना मैन्युअल प्रीमियम और लॉट आकार से होती है। जुड़े ब्रोकर के भाव ऑप्शन्स में दिखते हैं।",
"Notifications are unavailable until an alert delivery service is connected.":"अलर्ट भेजने की सेवा जुड़ने तक notifications उपलब्ध नहीं हैं।",
"No backtest report exists in this build. Results must be validated before relying on strategies.":"इस संस्करण में बैकटेस्ट रिपोर्ट नहीं है। रणनीति पर निर्भर होने से पहले परिणाम जाँचने होंगे।",
"Recent error types only; API secrets and response bodies are excluded.":"केवल हाल की त्रुटि के प्रकार; निजी API जानकारी और पूरे सर्वर जवाब शामिल नहीं हैं।",
"Backup excludes API credentials. Store it privately outside the app.":"बैकअप में API credentials नहीं हैं। इसे ऐप के बाहर सुरक्षित रखें।",
"Company/global headlines are context; earnings and exchange calendar are not connected.":"कंपनी/विश्व की खबरें संदर्भ हैं; earnings और एक्सचेंज कैलेंडर जुड़े नहीं हैं।",
"No news loaded for the selected symbol yet. Open Scanner and refresh.":"इस सिंबल की खबरें अभी नहीं मिलीं। स्कैनर खोलकर रीफ्रेश करें।",
"News: public RSS headlines; experimental phrase cues":"खबरें: सार्वजनिक RSS headlines; शब्दों पर प्रयोगात्मक संकेत",
"Waiting for candles and public news. Options require a verified broker feed.":"कैंडल और सार्वजनिक खबरों का इंतजार। ऑप्शन्स के लिए सत्यापित ब्रोकर डेटा चाहिए।",
"Combined status uses the same engine as Scanner; news headline cues are experimental; options may be unavailable.":"संयुक्त स्थिति स्कैनर के समान इंजन से आती है। खबरों के संकेत प्रयोगात्मक हैं; ऑप्शन डेटा उपलब्ध न भी हो।",
"Selected-source underlying candles • simulated premiums, not live contracts":"चुने स्रोत की मूल शेयर/इंडेक्स candles • अनुमानित प्रीमियम, वास्तविक live कॉन्ट्रैक्ट नहीं",
"Auto: Angel One first; Yahoo fallback for available underlying data. CE/PE requires a supported option feed. Options poll every 15 seconds while open during regular hours; not tick streaming. No live orders.":"Auto में Angel One पहले; उपलब्ध मूल डेटा के लिए Yahoo fallback। कॉल/पुट को समर्थित feed चाहिए। खुले ऑप्शन्स पेज पर बाजार समय में हर 15 सेकंड जाँच; tick streaming या live orders नहीं।",
"Option premium history • selected manual strike / CE or PE • 5m":"ऑप्शन प्रीमियम इतिहास • चुनी मैन्युअल स्ट्राइक / CE या PE • 5 मिनट",
"If chart loading fails, select BOT KING / Yahoo from Chart provider.":"चार्ट न खुले तो Chart provider में BOT KING / Yahoo चुनें।",
"Chart/Analysis/Both is selected per filter below. Only EMA currently has a chart overlay.":"हर फ़िल्टर के लिए चार्ट/विश्लेषण/दोनों नीचे चुनें। फिलहाल केवल EMA का चार्ट ओवरले है।",
"TradingView Lightweight Charts • source OHLC • ＋ / − / Reset or pinch • EMA 9/21 overlay only; other filters are analysis, not plotted overlays.":"TradingView चार्ट • स्रोत के OHLC • ＋ / − / Reset या pinch • केवल EMA 9/21 रेखाएँ; बाकी फ़िल्टर विश्लेषण में हैं।",
"Live position protection is NOT connected. Paper demonstration requires a manual current premium.":"वास्तविक पोजीशन सुरक्षा जुड़ी नहीं है। पेपर प्रदर्शन में वर्तमान प्रीमियम मैन्युअल चाहिए।",
"No live broker orders or background server are connected. This demo evaluates manually entered premiums while the app is open. It cannot protect real money or operate after the phone closes the app.":"Live orders या background server जुड़े नहीं हैं। यह डेमो ऐप खुला होने पर मैन्युअल प्रीमियम जाँचता है। ऐप बंद होने पर असली पैसे की सुरक्षा नहीं करता।",
"Paper limits are local simulations. Broker-side SL/target, filled-order confirmation and an always-on service are required before live automatic protection can be enabled.":"पेपर सीमाएँ स्थानीय अभ्यास हैं। Live सुरक्षा के लिए broker-side SL/लक्ष्य, भरे ऑर्डर की पुष्टि और लगातार चलने वाली सेवा चाहिए।",
"Paper daily entry limit and cumulative planned-stop-risk budget are enforced. EXIT stays available. Actual realized-loss accounting needs verified exit prices. Auto entry/re-entry, averaging, partial exits, trailing SL and square-off are saved plans only. No live orders.":"पेपर दैनिक एंट्री सीमा और नियोजित जोखिम बजट लागू हैं। EXIT उपलब्ध रहता है। वास्तविक लाभ/हानि के लिए सही निकास भाव चाहिए। ऑटो एंट्री, averaging, आंशिक निकास, trailing SL और square-off केवल सेव प्लान हैं।",
"Angel One • Connect sends credentials only to the official broker over HTTPS. Nothing is saved.":"Angel One • Connect पर credentials केवल official ब्रोकर को HTTPS से जाते हैं। इन्हें सेव नहीं किया जाता।",
"Angel One: read-only market data integration. Credentials go only to Angel One; public IP lookup uses ipify without credentials. No live orders. Other brokers are not integrated.":"Angel One: केवल डेटा पढ़ने का कनेक्शन। credentials सिर्फ Angel One को जाते हैं; ipify केवल public IP जाँचता है। Live orders नहीं। अन्य ब्रोकर अभी जुड़े नहीं हैं।",
"Analysis/Chart/Both routes a filter only to supported functions. Headline sentiment is experimental. WAIT can mean stale or missing data, not a sideways prediction.":"विश्लेषण/चार्ट/दोनों केवल समर्थित कामों पर फ़िल्टर लगाते हैं। खबरों का sentiment प्रयोगात्मक है। WAIT का कारण पुराना या गायब डेटा भी हो सकता है।",
"Analysis uses completed candles only; chart may show a forming candle.":"विश्लेषण केवल पूरी candles का है; चार्ट पर बन रही candle भी दिख सकती है।",
"Saved automatically":"अपने आप सेव हुआ","Saved on this device":"इस डिवाइस पर सेव हुआ","Save failed":"सेव नहीं हुआ",
"Language":"भाषा","English":"English","हिंदी":"हिंदी",
}
HI.update({"Auto":"ऑटो","Manual":"मैन्युअल","Paper":"पेपर","Semi-Auto":"अर्ध-ऑटो","Assisted":"सहायता मोड","Auto (Paper)":"ऑटो (पेपर)","Nearest":"निकटतम","Next":"अगली","Nearest (preview)":"निकटतम (अनुमान)","Next (preview)":"अगली (अनुमान)","Any":"कोई भी","Custom":"अपना","Analysis":"विश्लेषण","Chart":"चार्ट","Both":"दोनों","Candlestick":"कैंडल","Line":"लाइन","Auto trend":"ऑटो ट्रेंड","बंद करें":"बंद करें","अभी की स्थिति":"अभी की स्थिति","Lightweight chart: preparing...":"हल्का चार्ट तैयार हो रहा है…","Broker orders disabled. Paper Buy/Sell is simulated.":"ब्रोकर ऑर्डर बंद हैं। पेपर खरीद/बिक्री केवल अभ्यास है।"})
HI.update({
    "Live":"लाइव","Paper":"पेपर",
    "LIVE • Options, Orders & Positions":"लाइव • ऑप्शन्स, ऑर्डर और पोजीशन",
    "Paper • Practice only":"पेपर • केवल अभ्यास",
    "Settings • Broker & Data":"सेटिंग्स • ब्रोकर और डेटा",
    "Broker connection settings":"ब्रोकर कनेक्शन सेटिंग्स",
    "All simulation controls are on this page. No real broker orders are sent from Paper.":"अभ्यास के सभी नियंत्रण इस पेज पर हैं। पेपर से असली ब्रोकर ऑर्डर नहीं जाते।",
    "Broker data, option selection and real order controls are on this page. Paper practice is page 5.":"ब्रोकर डेटा, ऑप्शन चयन और असली ऑर्डर के नियंत्रण इसी पेज पर हैं। पेपर अभ्यास पाँचवें पेज पर है।",
    "Tap a CE or PE premium to select that exact contract for LIVE review.":"उसी कॉन्ट्रैक्ट की लाइव जाँच के लिए CE या PE प्रीमियम दबाएँ।",
"Verified CE/PE feed not connected. Simulated premiums are excluded.":"सत्यापित कॉल/पुट feed जुड़ी नहीं है। अनुमानित प्रीमियम इसमें शामिल नहीं हैं।",
"Save failed — device storage unavailable":"सेव नहीं हुआ — डिवाइस स्टोरेज उपलब्ध नहीं",
"WAITING FOR DATA • verified option-chain feed not connected":"डेटा का इंतजार • सत्यापित ऑप्शन चेन जुड़ी नहीं",
"No recent matching headlines / feed unavailable":"हाल की संबंधित खबर नहीं मिली / feed उपलब्ध नहीं",
"Yahoo candles unavailable; check connection or rate limits":"Yahoo candles नहीं मिलीं; कनेक्शन या request सीमा जाँचें",
"Option chart unavailable: connect Angel One and enter an exact listed strike/expiry.":"ऑप्शन चार्ट उपलब्ध नहीं: Angel One जोड़ें और सूचीबद्ध सही स्ट्राइक/एक्सपायरी भरें।",
"Feed unavailable. Check connection and listed expiry; cached quotes retain their timestamps.":"Feed उपलब्ध नहीं। कनेक्शन और सूचीबद्ध एक्सपायरी जाँचें; पुराने भाव अपने समय के साथ दिखते हैं।",
"Connection failed. Check credentials, TOTP, API permissions and network. Auto remains available.":"कनेक्शन नहीं हुआ। credentials, TOTP, API अनुमति और नेटवर्क जाँचें। Auto मोड उपलब्ध है।",
"Timeout reached, but manual mark is stale — PAPER auto exit blocked. Supply a current mark or confirm exit manually.":"इंतजार पूरा, लेकिन मैन्युअल भाव पुराना है — पेपर ऑटो निकास रोका गया। नया भाव दें या मैन्युअल निकास की पुष्टि करें।",
"PAUSED — broker feed not connected":"रुका है — ब्रोकर feed जुड़ी नहीं",
"Refresh failed • last results may be stale":"रीफ्रेश नहीं हुआ • पिछले परिणाम पुराने हो सकते हैं",
"Yahoo option history unavailable":"Yahoo ऑप्शन इतिहास उपलब्ध नहीं",
"Incomplete volume coverage; totals unavailable.":"वॉल्यूम डेटा अधूरा; कुल आँकड़े उपलब्ध नहीं।",
"Cannot simulate entry: Yahoo quote unavailable.":"पेपर एंट्री नहीं हुई: Yahoo भाव उपलब्ध नहीं।",
"OI / PCR / Max Pain: unavailable until verified option-chain API is connected.":"OI / PCR / Max Pain: सत्यापित ऑप्शन चेन API जुड़ने तक उपलब्ध नहीं।",
"Yahoo Finance unavailable: check internet / rate limits":"Yahoo Finance उपलब्ध नहीं: इंटरनेट / request सीमा जाँचें",
"Broker feed failed; reconnect or select Auto":"ब्रोकर feed नहीं मिली; फिर जोड़ें या Auto चुनें",
"Yahoo preview • delayed or unavailable":"Yahoo उदाहरण • देरी या डेटा उपलब्ध नहीं",
"OI/PCR/Max Pain not connected; unavailable filters never vote.":"OI/PCR/Max Pain जुड़े नहीं; डेटा बिना फ़िल्टर वोट नहीं देते।",
"Analysis uses completed candles only; chart may show a forming candle.":"विश्लेषण में केवल पूरी candles हैं; चार्ट में बनती candle भी दिख सकती है।",
})
HI.update({
"SUPER FIVE • LAST AVAILABLE ANALYSIS":"सुपर फाइव • आखिरी उपलब्ध विश्लेषण",
"Configured 50-company watchlist • last completed-candle analysis • not a trade order":"सेव सूची की 50 कंपनियाँ • आखिरी पूरी कैंडल का विश्लेषण • ट्रेड ऑर्डर नहीं",
"Historical conclusions are kept for reference. Freshness checks still gate new live signals.":"पुराने निष्कर्ष जानकारी के लिए रहते हैं। नए live संकेत के लिए ताजा डेटा की जाँच जरूरी है।",
"Last available option quotes • timestamps below • not a live connection guarantee":"आखिरी उपलब्ध ऑप्शन भाव • समय नीचे देखें • live कनेक्शन की गारंटी नहीं",
"No saved analysis; waiting for first successful fetch":"सेव विश्लेषण नहीं; पहली सफल डेटा जाँच का इंतजार",
"No valid candle data":"सही कैंडल डेटा उपलब्ध नहीं",
"Time unavailable":"समय उपलब्ध नहीं","Invalid future time":"भविष्य का गलत समय",
})
HI.update({
"EXECUTION CAPABILITIES":"काम करने की वास्तविक क्षमता",
"Market data: Yahoo / saved data; broker not connected":"बाजार डेटा: Yahoo / सेव डेटा; ब्रोकर जुड़ा नहीं",
"Market data: Angel One authenticated":"बाजार डेटा: Angel One login जुड़ा है",
"Paper orders: local simulation • strategy switches: saved plans":"पेपर ऑर्डर: स्थानीय अभ्यास • रणनीति स्विच: सेव प्लान",
"Live orders: OFF • live SL/target: OFF • server automation: NOT CONNECTED":"असली ऑर्डर: बंद • असली SL/लक्ष्य: बंद • सर्वर ऑटोमेशन: जुड़ा नहीं",
"Phone lock: uninterrupted monitoring is NOT guaranteed. Display ON does not enable live trading.":"फोन लॉक: लगातार निगरानी की गारंटी नहीं। स्क्रीन चालू रखने से live ट्रेडिंग चालू नहीं होती।",
"Live auto trading • not available":"वास्तविक ऑटो ट्रेडिंग • अभी उपलब्ध नहीं",
"While-open monitoring only; screen-lock continuity is not verified":"केवल ऐप खुला रहने पर निगरानी; लॉक में लगातार चलना सत्यापित नहीं",
"App backgrounded • uninterrupted monitoring unavailable • refresh on resume":"ऐप बैकग्राउंड में • लगातार निगरानी उपलब्ध नहीं • लौटने पर रीफ्रेश",
"App resumed • checking selected data...":"ऐप फिर खुला • चुना डेटा जाँच रहे हैं…",
"App resumed • selected data checked • no automatic broker order":"ऐप फिर खुला • चुना डेटा जाँचा • कोई ऑटो ब्रोकर ऑर्डर नहीं",
"App resumed • refresh failed; last saved data remains visible":"ऐप फिर खुला • रीफ्रेश नहीं हुआ; पिछला डेटा दिखता रहेगा",
"Retry current data":"वर्तमान डेटा फिर जाँचें",
"Paper simulation":"पेपर अभ्यास",
"No request recorded for this selection yet":"इस चयन के लिए इस सत्र में डेटा प्रयास दर्ज नहीं",
"Market quotes":"बाजार भाव","Analysing configured companies":"चुनी कंपनियों का विश्लेषण",
"No valid data; last saved results retained":"सही डेटा नहीं मिला; पिछले परिणाम रखे गए",
})
EN_STATUS={
 "बंद करें":"Close","अभी की स्थिति":"Current status",
 "आसान जानकारी और वर्तमान स्थिति":"Simple explanation and current status","जानकारी":"Information",
 "डेटा न मिले: Refresh करें, स्रोत और expiry जाँचें। Field error हो: मान ठीक करके फिर save करें।":"If data is missing, refresh and check the source and expiry. For a field error, correct its value and save again.",
 "निजी credential field है। Popup में इसका मान नहीं दिखाया जाता।":"Private credential field. Its value is never displayed in this popup.",
 "इस field में validation error है: ":"This field has a validation error: ",
 "इस नियंत्रण में अभी validation error दर्ज नहीं है। वास्तविक डेटा की स्थिति संबंधित सेक्शन में देखें।":"No validation error is currently recorded for this control. Check actual data status in the relevant section.",
 "इस सत्र में दर्ज errors: ":"Recorded errors in this session: ",
 "। यह पूर्ण कार्यक्षमता का प्रमाण नहीं है।":". This does not prove complete functionality.",
 "यह सेवा अभी जुड़ी नहीं है।":"This service is not connected.",
 "Paper / saved-plan सुविधा है। Live orders और live automatic exit सक्रिय नहीं हैं।":"Paper / saved-plan feature. Live orders and live automatic exit are not enabled.",
 "Verified option डेटा अभी उपलब्ध नहीं है। ":"Verified option data is currently unavailable. ",
 "हाल के option quotes उपलब्ध हैं। ":"Recent option quotes are available. ",
 "Option quotes पुराने हैं या समय उपलब्ध नहीं है। ":"Option quotes are stale or their timestamps are unavailable. ",
 "Headlines अभी उपलब्ध नहीं हैं।":"Headlines are currently unavailable.",
 "Analysis अभी उपलब्ध नहीं है।":"Analysis is currently unavailable.",
 " • स्रोत: ":" • Source: "," • broker ":" • Broker: ","जुड़ा है":"connected","जुड़ा नहीं है":"disconnected",
}
HI.update({
 "Every section below uses the selected symbol and expiry. CE/PE prices, OI and PCR require a verified broker feed; blank values are not zero.":"नीचे के सभी सेक्शन चुने सिंबल और एक्सपायरी के हैं। CE/PE भाव, OI और PCR के लिए सत्यापित ब्रोकर डेटा चाहिए। खाली मान शून्य नहीं हैं।",
 "Protection: Manual • paper demonstration only; live monitoring disconnected":"सुरक्षा: मैन्युअल • केवल पेपर प्रदर्शन; live निगरानी जुड़ी नहीं",
 "Connecting Yahoo Finance… • Public news fetched separately; option status is shown on Options":"Yahoo Finance जुड़ रहा है… • सार्वजनिक खबरें अलग आती हैं; ऑप्शन स्थिति ऑप्शन्स में देखें",
 "Updated — • 5m candle ranking using active scanner filters; NOT a win probability":"अपडेट — • सक्रिय फ़िल्टर से 5 मिनट कैंडल क्रम; जीत की संभावना नहीं",
 "Options help":"ऑप्शन्स की जानकारी","Risk and protection help":"जोखिम और सुरक्षा की जानकारी","Scanner help":"स्कैनर की जानकारी",
 "TOTP (current 6-digit code)":"TOTP (अभी का 6 अंकों का कोड)","Client Code":"क्लाइंट कोड",
 "OI Resistance":"OI प्रतिरोध","OI Support":"OI समर्थन","OI Profile":"OI प्रोफाइल",
 "SMC Structure":"SMC संरचना","Order Block":"ऑर्डर ब्लॉक","Liquidity Sweep":"लिक्विडिटी स्वीप",
 "Pivot Points":"पिवट स्तर","Bull Call Spread":"बुल कॉल स्प्रेड","Bear Put Spread":"बेयर पुट स्प्रेड","Iron Condor":"आयरन कॉन्डोर",
 "Filter agreement is not success probability":"फ़िल्टर का मेल सफलता की संभावना नहीं है",
 "Completed candles are stale":"पूरी कैंडल का डेटा पुराना है","Need 30 completed valid candles":"कम से कम 30 पूरी और सही कैंडल चाहिए",
 "Invalid OHLC or volume values":"OHLC या वॉल्यूम मान गलत हैं","Duplicate or unordered candle timestamps":"कैंडल का समय दोहराया या उलटा है",
 "Future candle timestamp":"कैंडल का समय भविष्य का है",
})
PREFIX={
"DATA UNAVAILABLE — ":"डेटा उपलब्ध नहीं — ","Underlying: ":"मूल शेयर/इंडेक्स: ","Viewing: ":"देख रहे हैं: ",
"Selected: ":"चुना: ","Provider: ":"स्रोत: ","Total unrealized P&L ":"कुल खुला लाभ/हानि ",
"Last successful scan: ":"अंतिम सफल स्कैन: ","Candle age: ":"कैंडल की उम्र: ","Next refresh: ":"अगला रीफ्रेश: ",
"Selected strategy: ":"चुनी रणनीति: ","Remaining planned-risk budget: ":"बाकी नियोजित जोखिम बजट: ",
"Entries: ":"एंट्री: ","ADDED FILTERS • ":"जोड़े फ़िल्टर • ","Active: ":"सक्रिय: ",
"CANDLE ANALYSIS • ":"कैंडल विश्लेषण • ","COMBINED ANALYSIS • ":"संयुक्त विश्लेषण • ",
"LIGHTWEIGHT CHART • ":"हल्का चार्ट • ","OPTIONS DATA • ":"ऑप्शन डेटा • ",
"WAIT • no fresh qualified candidates; not a trade guarantee":"WAIT • ताजा योग्य चयन नहीं; ट्रेड की गारंटी नहीं",
"Broker data: disconnected • live orders: disabled":"ब्रोकर डेटा: जुड़ा नहीं • live orders: बंद",
"Analysis Basis":"विश्लेषण का आधार","ANALYSIS BASIS • ":"विश्लेषण का आधार • ",
"Candle ":"कैंडल "," candles":" कैंडल","Data quality: ":"डेटा गुणवत्ता: ",
"OI/PCR unavailable: incomplete strike-window coverage.":"OI/PCR उपलब्ध नहीं: चुनी स्ट्राइक का डेटा अधूरा है।",
"Cached quotes are old; live OI/PCR calculation paused.":"कैश किए भाव पुराने हैं; live OI/PCR गणना रुकी है।",
"Recent quote":"हाल का भाव","Option quote times (IST): ":"ऑप्शन भाव का समय (IST): ",
"Loading selected data...":"चुना डेटा लोड हो रहा है…","Complete":"पूरा","Unavailable":"उपलब्ध नहीं",
"Not connected. Authentication adapter required for ":"कनेक्ट नहीं। समर्थित login चाहिए: ",
"Recent quote":"हाल का भाव","Old / delayed quote":"पुराना / देर का भाव","quote time unavailable":"भाव का समय उपलब्ध नहीं",
"HISTORICAL / last available":"ऐतिहासिक / आखिरी उपलब्ध","Recent analysis":"हाल का विश्लेषण",
"Last saved quote":"आखिरी सेव भाव","Source: ":"स्रोत: ","HISTORICAL":"ऐतिहासिक",
"DATA UNAVAILABLE":"डेटा उपलब्ध नहीं","BULLISH":"बुलिश","BEARISH":"बेयरिश",
"Scan progress: ":"जाँच प्रगति: "," • valid: ":" • सही डेटा: "," • cached: ":" • सेव डेटा: "," • failed: ":" • असफल: ",
" • saved preference; no live orders":" • सेव प्राथमिकता; असली ऑर्डर नहीं",
" • data time: ":" • डेटा समय: "," • last attempt: ":" • अंतिम प्रयास: "," • last success: ":" • अंतिम सफलता: ",
"Authentication required; reconnect broker":"पहचान सत्यापन चाहिए; ब्रोकर फिर जोड़ें",
"Broker session expired; reconnect":"ब्रोकर session समाप्त; फिर जोड़ें",
"Network timeout":"नेटवर्क ने समय पर जवाब नहीं दिया",
"Provider request limit; retry later":"स्रोत की request सीमा; बाद में फिर जाँचें",
"This source has no verified NSE option-chain data":"इस स्रोत में सत्यापित NSE ऑप्शन चेन डेटा नहीं",
"No recent headlines or feed unavailable":"हाल की खबर नहीं मिली या feed उपलब्ध नहीं",
"Quote time is old, missing or invalid; historical display only":"भाव का समय पुराना/गायब/गलत; केवल ऐतिहासिक प्रदर्शन",
" • source: ":" • स्रोत: ","Last cache write: ":"आखिरी डेटा सेव की स्थिति: ",
"UNAVAILABLE":"उपलब्ध नहीं","AVAILABLE":"उपलब्ध","FALLBACK":"वैकल्पिक स्रोत","CACHED":"सेव डेटा","STALE":"पुराना","PARTIAL":"अधूरा","LOADING":"लोड हो रहा है",
}
HI.update({'Segment': 'सेगमेंट', 'Cash': 'कैश शेयर', 'Plan side': 'प्लान की दिशा', 'Cash shares': 'कैश शेयरों की संख्या', 'Maximum total cash shares': 'कुल अधिकतम कैश शेयर', 'I verified manual contract, lot size and premium • Paper only': 'मैंने कॉन्ट्रैक्ट, लॉट साइज और भाव जाँचा है • केवल पेपर', 'Paper capital (INR)': 'पेपर पूँजी (₹)', 'Max paper notional per position (not margin)': 'प्रति पोजीशन अधिकतम पेपर मूल्य (मार्जिन नहीं)', 'Max planned risk per trade (INR)': 'प्रति ट्रेड अधिकतम नियोजित जोखिम (₹)', 'Max planned risk per trade (%)': 'प्रति ट्रेड अधिकतम नियोजित जोखिम (%)', 'Manual exit price • optional; blank means unknown': 'मैनुअल निकास भाव • खाली होने पर अज्ञात', 'Paper charges (INR) • 0 excludes charges': 'पेपर शुल्क (₹) • 0 पर शुल्क शामिल नहीं', 'Maximum paper additions': 'अधिकतम पेपर अतिरिक्त एंट्री', 'Lots / shares per addition': 'हर अतिरिक्त एंट्री में लॉट / शेयर', 'Paper trailing price distance (%)': 'पेपर ट्रेलिंग भाव दूरी (%)', 'Paper partial profit trigger (%)': 'पेपर आंशिक मुनाफे की सीमा (%)', 'Paper partial quantity (%)': 'पेपर आंशिक निकास मात्रा (%)', 'Allow paper re-entry after stop-loss': 'स्टॉप लॉस के बाद पेपर री-एंट्री की अनुमति', 'PAPER BOT • MANUAL TICK ENGINE': 'पेपर बॉट • मैनुअल भाव इंजन', 'Start Paper': 'पेपर शुरू करें', 'Pause': 'रोकें', 'Stop new actions': 'नई कार्रवाइयाँ बंद करें', 'Process manual mark': 'मैनुअल भाव पर कार्रवाई करें', 'Current PAPER price • manually supplied': 'वर्तमान पेपर भाव • खुद दर्ज करें', 'Entry when Paper Start is pressed': 'पेपर शुरू करने पर एंट्री', 'Paper re-entry on a new manual tick': 'नए मैनुअल भाव पर पेपर री-एंट्री', 'Paper averaging on manual ticks • BUY only': 'मैनुअल भाव पर पेपर एवरेजिंग • केवल BUY', 'Paper partial profit on manual ticks': 'मैनुअल भाव पर आंशिक पेपर मुनाफा', 'Trailing stop • paper manual ticks': 'ट्रेलिंग स्टॉप • मैनुअल पेपर भाव', '04  PAPER STRATEGY • MANUAL TICKS': '04  पेपर रणनीति • मैनुअल भाव', 'Start never enables real orders. Each Process mark press supplies one new manual price; phone lock pauses this engine. Stop blocks strategy actions but does not close a position.': 'Start से असली ऑर्डर चालू नहीं होते। हर बटन दबाने पर नया मैनुअल भाव लिया जाएगा। फोन लॉक होने पर इंजन रुकता है। Stop नई रणनीति कार्रवाइयाँ रोकता है, पोजीशन बंद नहीं करता।', 'Paper bot stopped • no live orders • manual marks required': 'पेपर बॉट बंद • असली ऑर्डर नहीं • मैनुअल भाव चाहिए'})
HI.update({
    "SELECTED SYMBOL • FINAL CANDLE DIRECTION":"चुना शेयर / इंडेक्स • अंतिम कैंडल दिशा",
    "Candle-filter agreement, not success probability. Higher timeframe is a separate check; Super Five remains separate.":"यह कैंडल फ़िल्टरों की सहमति है, जीत की संभावना नहीं। बड़े timeframe की पुष्टि और Super Five अलग हैं।",
    "Higher timeframe confirmation: not configured for daily candles.":"दैनिक कैंडल के ऊपर बड़े timeframe की पुष्टि अभी निर्धारित नहीं है।",
    "Higher timeframe confirmation: current selected signal unavailable.":"बड़े timeframe की पुष्टि: चुने timeframe का वर्तमान संकेत उपलब्ध नहीं है।",
    "Refresh the selected symbol and timeframe. No current signal yet.":"चुने शेयर और timeframe को रीफ्रेश करें। अभी वर्तमान संकेत नहीं मिला है।",
})
PREFIX.update({
    "Bullish: ":"बुलिश: ","Bearish: ":"बेरिश: ","Neutral: ":"न्यूट्रल: ","Unavailable: ":"अनुपलब्ध: ",
    "Available filters: ":"उपलब्ध फ़िल्टर: ","directional agreement: ":"दिशा देने वाले फ़िल्टरों की सहमति: ",
    "required: ":"जरूरी: ","Completed candle: ":"पूरी कैंडल: ",
    "Higher timeframe ":"बड़ा timeframe ","Recent completed candles":"हाल की पूरी कैंडल",
    "HISTORICAL / stale or refresh failed":"ऐतिहासिक / पुराना डेटा या रीफ्रेश असफल",
    "Awaiting selected analysis":"चुने शेयर के विश्लेषण की प्रतीक्षा", "AGREES":"सहमत", "CONFLICT":"विपरीत दिशा", "UNCONFIRMED":"पुष्टि नहीं",
})

HI.update({
"BROKER & API STATUS":"ब्रोकर और API स्थिति",
"Angel One API — Connected":"Angel One API — जुड़ा हुआ",
"Angel One API — Disconnected":"Angel One API — जुड़ा नहीं",
"Refresh data / account":"डेटा / खाता रीफ्रेश करें",
"Connection settings":"कनेक्शन सेटिंग्स",
"Disconnect":"डिस्कनेक्ट करें",
"LIVE MANUAL ORDERS":"लाइव मैनुअल ऑर्डर",
"Use fresh API prices for Paper while open":"ऐप खुला रहने पर पेपर में ताजा API भाव लें",
"Use broker price / process paper tick":"ब्रोकर भाव लेकर पेपर जाँचें",
"API marking OFF • manual practice available":"API भाव से जाँच बंद • मैनुअल अभ्यास उपलब्ध",
"Enter a numeric practice price":"अभ्यास का भाव संख्या में भरें",
"Angel One API connected. Login fields hidden; credentials are not saved.":"Angel One API जुड़ा है। लॉगिन बॉक्स छिपे हैं; निजी जानकारी सेव नहीं होती।",
"Broker data • v2.3.0":"ब्रोकर डेटा • v2.3.0",
})
PREFIX.update({"Candle direction: ":"कैंडल दिशा: ","Three-source check: ":"तीन स्रोतों की जाँच: ","Options: ":"ऑप्शन: "})

def translate(text,language):
    text=str(text)
    if language!="हिंदी":
        result=text
        for old,new in sorted(EN_STATUS.items(),key=lambda x:-len(x[0])):result=result.replace(old,new)
        return result
    if text in HI:return HI[text]
    if text.startswith("ⓘ "):return "ⓘ "+translate(text[2:],language)
    result=text
    for old,new in sorted(PREFIX.items(),key=lambda x:-len(x[0])):result=result.replace(old,new)
    for old,new in [("sec old","सेकंड पुराना"),("min old","मिनट पुराना"),("hours old","घंटे पुराना"),("days old","दिन पुराना")]:result=result.replace(old,new)
    if re.fullmatch(r"\d+ Lots?",result):return result.split()[0]+" लॉट"
    return result

def localize_tree(control,language):
    # Keep originals separately so switching language is reversible and dynamic
    # status updates are not overwritten by a previous translation.
    import flet as ft
    attrs=[]
    if isinstance(control,ft.Text):attrs.append("value")
    if isinstance(control,(ft.TextButton,ft.ElevatedButton,ft.OutlinedButton)):attrs.append("text")
    if isinstance(control,ft.dropdown.Option):
        if control.text is None:control.text=control.key
        attrs.append("text")
    if isinstance(control,(ft.TextField,ft.Dropdown,ft.Checkbox,ft.Switch)):
        attrs += ["hint_text"] if getattr(control,"_bk_external_label",False) else ["label","hint_text"]
    for attr in attrs:
        try:value=getattr(control,attr,None)
        except AttributeError:continue
        if not isinstance(value,str):continue
        original=getattr(control,"_bk_original_"+attr,value)
        last=getattr(control,"_bk_last_"+attr,None)
        if last is not None and value!=last:original=value
        setattr(control,"_bk_original_"+attr,original)
        translated=translate(original,language)
        setattr(control,attr,translated);setattr(control,"_bk_last_"+attr,translated)
    for child in control._get_children():localize_tree(child,language)


