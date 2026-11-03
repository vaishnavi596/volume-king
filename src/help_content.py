"""Hindi explanations shared by section and field help."""
def describe(label):
    text=str(label).lower()
    rules=[
      (("premium budget",),"यह premium की चुनी हुई सीमा है। Scanner इसी सीमा में simulation candidates छाँटता है। यह पूरे trade का कुल खर्च या उपलब्ध broker balance नहीं है।"),
      (("refresh","auto scan"),"यह ऐप खुला रहने पर तय अंतराल में डेटा दोबारा जाँचता है। बाजार बंद होने पर automatic refresh रुक सकता है। यह background service या tick-by-tick streaming नहीं है।"),
      (("period","history"),"यह इतिहास की अवधि है। Timeframe एक candle की अवधि है। स्रोत के अनुसार intraday history सीमित हो सकती है।"),
      (("symbol","instrument","index / stock"),"यह किस शेयर या index का डेटा देखना है, उसका चुनाव है। Symbol जोड़ने से उस पर option contract उपलब्ध होना सिद्ध नहीं होता।"),
      (("pcr","put call ratio"),"PCR, Put और Call के Open Interest का अनुपात है। यहाँ अधिकतम 9 चुने हुए strikes का अनुपात है, पूरी option chain का नहीं। अकेले इससे खरीद या बिक्री तय नहीं होती।"),
      (("oi analysis","open interest","oi support","oi resistance","oi profile"),"Open Interest खुले contracts की संख्या बताता है। ज्यादा OI अपने आप bullish या bearish नहीं होता। सही expiry, coverage और डेटा का समय देखें।"),
      (("option chart","premium chart"),"यह चुने हुए strike, expiry और CE/PE के premium का इतिहास है। यह underlying index का chart नहीं है। Angel One से सूचीबद्ध contract का डेटा चाहिए।"),
      (("option chain","options data"),"एक expiry के Call और Put premium, strike तथा OI दिखते हैं। खाली खाने का मतलब उपलब्ध डेटा नहीं है; इसका मतलब शून्य नहीं है।"),
      (("flow","activity","volume"),"यह कारोबार की गतिविधि बताता है। Call या Put में ज्यादा volume होने से यह तय नहीं होता कि खरीद हुई, बिक्री हुई या लोगों को profit हुआ।"),
      (("source","provider","broker","market data","data mode"),"Auto मोड में जुड़े Angel One को प्राथमिकता मिलती है। जरूरत पर उपलब्ध underlying डेटा Yahoo से मिलता है। Yahoo से इस ऐप को verified NSE option chain नहीं मिलती। डेटा का समय देखें। असली orders नहीं भेजे जाते।"),
      (("combined","analysis basis","candle analysis","super five","top 5","scanner","signal filter"),"यह नियम आधारित analysis है, प्रशिक्षित AI मॉडल नहीं। candles और चुने हुए filters जाँचे जाते हैं। अधूरे, पुराने या विरोधी संकेत होने पर WAIT दिखता है। Filter agreement सफलता की संभावना नहीं है।"),
      (("ema","sma"),"यह चलती औसत से trend का संकेत देता है। छोटा और बड़ा average तुलना में काम आते हैं। Sideways बाजार में गलत संकेत हो सकते हैं।"),
      (("rsi",),"RSI हाल की तेजी और कमजोरी का संकेत है। बहुत ऊँचा या नीचा RSI होने से अपने आप reversal पक्का नहीं होता।"),
      (("macd",),"MACD चलती औसत और signal line का अंतर देखता है। दूसरे संकेत और डेटा की गुणवत्ता के साथ समझें।"),
      (("vwap",),"VWAP, कारोबार की मात्रा के अनुसार सत्र का औसत भाव है। Volume न मिले तो यह filter उपलब्ध नहीं होता और vote नहीं देता।"),
      (("supertrend","atr"),"ATR कीमत की हलचल मापता है। Supertrend उसी से trend का नियम बनाता है। तेज उलटफेर या sideways बाजार में गलत संकेत संभव हैं।"),
      (("smc","order block","fvg","liquidity","pivot"),"यह candles पर आधारित संभावित structure या price zone है। यह संस्थागत खरीद-बिक्री का प्रमाण या पक्की entry नहीं है।"),
      (("expiry",),"Expiry चुनें। Broker जुड़ा हो तो सूचीबद्ध expiry इस्तेमाल होती है। Calendar preview की तारीख अपने आप exchange-verified contract नहीं बनती।"),
      (("strike",),"Strike, option contract का तय exercise price है। सही index, expiry और CE/PE के साथ सूचीबद्ध strike चुनें।"),
      (("lot","quantity","lots"),"Lots और units per lot मिलकर कुल quantity बनाते हैं। सही lot size contract से जाँचें; गलत संख्या risk और P&L बदल देगी।"),
      (("stop","risk","loss","target","profit","protection"),"यह जोखिम या लाभ की सीमा है। वर्तमान protection केवल paper demonstration है और manual premium पर काम करता है। यह live broker position को अपने आप बंद नहीं करता।"),
      (("paper","position","trade","mode","strategy","re-entry","entry","dip","square"),"वर्तमान trading controls paper simulation या saved plan हैं। असली broker orders नहीं जाते। Manual premium, lot size और contract पहले जाँचें।"),
      (("alerts",),"इस build में बाहर notification भेजने की सेवा नहीं जुड़ी है। केवल स्क्रीन पर जानकारी दिखना push alert नहीं है।"),
      (("backtest",),"इस build में पूरा backtest engine नहीं जुड़ा है। Historical chart या indicator agreement को backtest profit न समझें।"),
      (("diagnostic",),"यह हाल की त्रुटियों के प्रकार दिखाता है। कोई error दर्ज न होने से सभी features का काम करना सिद्ध नहीं होता। Credentials या पूरा server response यहाँ नहीं दिखाया जाता।"),
      (("news","headline"),"यह हाल की headlines पर प्रयोगात्मक positive/negative संकेत है। पूरी खबर का संदर्भ या बाजार पर प्रभाव सिद्ध नहीं होता।"),
      (("api key","mpin","totp","client code","token","credential"),"यह broker connection की निजी जानकारी है। इसे साझा न करें। Connect दबाने पर जानकारी official Angel One को HTTPS से जाती है; ऐप इसे स्थायी रूप से save नहीं करता।"),
      (("chart","candlestick","timeframe","candle"),"Chart चुने हुए symbol और timeframe की candles दिखाता है। खुली candle बदल सकती है; analysis में पूरी हुई candles इस्तेमाल होती हैं। ⓘ में डेटा की वर्तमान स्थिति देखें।"),
      (("save","backup","restore","undo"),"सामान्य settings डिवाइस पर save होती हैं। Backup में broker secrets शामिल नहीं होते। Restore पर automatic protection बंद रहता है।"),
    ]
    for keywords,message in rules:
        if any(word in text for word in keywords):return message
    return "यह नियंत्रण अपने label के अनुसार चयन या गणना बदलता है। सामान्य settings डिवाइस पर save होती हैं। डेटा न मिलने पर खाली खाने को वास्तविक शून्य न समझें।"
