async def loadchart(e=None):
        chartcol.controls=[ft.Text("चार्ट लोड हो रहा है...",color=MUTED)]; page.update()
        try:
            rows=await asyncio.to_thread(candles,chartsym.value,interval.value)
            if not rows: raise ValueError()
            vals=[x["close"] for x in rows]; low,high=min(vals),max(vals); glyph="▁▂▃▄▅▆▇█"
            spark="".join(glyph[min(7,int((v-low)/(high-low)*7))] if high>low else "▄" for v in vals)
            chartcol.controls=[ft.Text(spark,size=24,color=GOLD),
                ft.Text("Time   Open    High    Low    Close    Volume",size=10,color=MUTED)]
            for x in rows[-15:]:
                chartcol.controls.append(ft.Text(f'{x["time"]}  {x["open"]:.2f}  {x["high"]:.2f}  {x["low"]:.2f}  {x["close"]:.2f}  {int(x["volume"])}',size=10))
        except Exception:
            chartcol.controls=[ft.Text("NO DATA • Yahoo candle data उपलब्ध नहीं है।",color=RED)]
        page.update()

    async def loadoptions(e=None):
        optcol.controls=[ft.Text("Options chain जाँची जा रही है...",color=MUTED)]; page.update()
        try:
            d=await asyncio.to_thread(option_chain,optsym.value)
            optcol.controls=[card("Expiry",d["expiry"]),
                card("PCR (Put OI / Call OI)",f'{d["pcr"]:.2f}' if d["pcr"] is not None else "NO DATA"),
                card("Max Pain",f'{d["maxpain"]:,.2f}' if d["maxpain"] is not None else "NO DATA"),
                card("Call OI",f'{d["coi"]:,}'),card("Put OI",f'{d["poi"]:,}'),
                ft.Text("CE / PE Premium और OI (पहले 8 strikes)",weight=ft.FontWeight.BOLD)]
            c={x["strike"]:x for x in d["calls"]}; p={x["strike"]:x for x in d["puts"]}
            for k in sorted(set(c)|set(p))[:8]:
                a=c.get(k,{}); b=p.get(k,{})
                optcol.controls.append(ft.Text(f'{k:g} | CE ₹{a.get("lastPrice","--")} OI {a.get("openInterest","--")} | PE ₹{b.get("lastPrice","--")} OI {b.get("openInterest","--")}',size=11))
            optcol.controls.append(ft.Text("PCR/Max Pain उपलब्ध chain से गणना हैं, ट्रेड सिग्नल नहीं।",size=10,color=MUTED))
        except Exception:
            optcol.controls=[ft.Text("NO DATA • Yahoo पर इस NSE symbol की options chain उपलब्ध नहीं है।",color=RED),
                ft.Text("भारतीय index options का डेटा Yahoo पर अक्सर उपलब्ध नहीं होता।",size=11,color=MUTED)]
        page.update()

    def buy(e):
        try:
            p=float(prem.value); n=int(qty.value)
            if p<=0 or n<=0: raise ValueError()
            trades.append({"symbol":tsym.value,"side":side.value,"qty":n,"entry":p,"exit":None})
            render(); page.update()
        except Exception: status.value="Premium और Quantity सही डालें"; page.update()

    def exittrade(i):
        try:
            p=float(prem.value)
            if p<0: raise ValueError()
            trades[i]["exit"]=p; render(); page.update()
        except Exception: status.value="Exit Premium सही डालें"; page.update()

    def render():
        body.controls=[]
        if active=="Dashboard":
            qcards.controls=[]
            for s in ("NIFTY","BANKNIFTY","SENSEX"):
                q=quotes.get(s)
                qcards.controls.append(card(s,f'{q["price"]:,.2f}',f'{q["change"]:+.2f}%' if q and q["change"] is not None else "NO DATA") if q else card(s,"NO DATA","Yahoo quote नहीं मिला"))
            body.controls=[ft.Text("Market Dashboard",size=19,weight=ft.FontWeight.BOLD),qcards,
                ft.ElevatedButton("↻ Refresh Market",on_click=lambda e:page.run_task(refresh),bgcolor=GOLD,color="#08111F"),
                ft.Text("Yahoo Finance अनौपचारिक स्रोत है; एक्सचेंज का आधिकारिक लाइव फीड नहीं।",size=11,color=MUTED)]
        elif active=="Watchlist":
            body.controls=[ft.Text("Watchlist • NIFTY 50",size=19,weight=ft.FontWeight.BOLD),
                ft.Row([addfield,ft.ElevatedButton("Add",on_click=addstock,bgcolor=GOLD,color="#08111F")])]
            watchcol.controls=[]
            for s in watch:
                q=quotes.get(s); price=f'{q["price"]:,.2f}' if q else "--"
                change=f'{q["change"]:+.2f}%' if q and q["change"] is not None else "भाव के लिए Load दबाएँ"
                watchcol.controls.append(ft.Container(ft.Row([
                    ft.Column([ft.Text(s,weight=ft.FontWeight.BOLD),ft.Text(change,size=10,color=MUTED)],expand=True,spacing=2),
                    ft.Text(price,color=GOLD),ft.TextButton("Load",on_click=lambda e,x=s:page.run_task(loadquote,x)),
                    ft.TextButton("×",on_click=lambda e,x=s:remove(x))]),bgcolor=CARD,padding=8,border_radius=8))
            body.controls.append(watchcol)
        elif active=="Options":
            body.controls=[ft.Text("Options Chain • Yahoo",size=19,weight=ft.FontWeight.BOLD),
                ft.Row([optsym,ft.ElevatedButton("Load Chain",on_click=loadoptions,bgcolor=GOLD,color="#08111F")]),optcol]
        elif active=="Charts":
            body.controls=[ft.Text("Market Charts",size=19,weight=ft.FontWeight.BOLD),
                ft.Row([chartsym,interval]),ft.ElevatedButton("Load Chart",on_click=loadchart,bgcolor=GOLD,color="#08111F"),chartcol]
        elif active=="Paper":
            opened=sum(t["exit"] is None for t in trades)
            pnl=sum((t["exit"]-t["entry"])*t["qty"] for t in trades if t["exit"] is not None)
            tradecol.controls=[card("Open Trades",str(opened)),card("Realized P&L",f"₹{pnl:,.2f}"),
                ft.Text("नया Paper Trade",weight=ft.FontWeight.BOLD),ft.Row([tsym,side]),ft.Row([prem,qty]),
                ft.ElevatedButton("BUY (PAPER)",on_click=buy,bgcolor=GOLD,color="#08111F"),
                ft.Text("Trade History",weight=ft.FontWeight.BOLD)]
            for i,t in enumerate(trades):
                line=f'{t["symbol"]} {t["side"]} | Qty {t["qty"]} | Entry ₹{t["entry"]:.2f}'
                if t["exit"] is None:
                    tradecol.controls.append(ft.Row([ft.Text(line,size=11,expand=True),ft.TextButton("Exit",on_click=lambda e,j=i:exittrade(j))]))
                else:
                    value=(t["exit"]-t["entry"])*t["qty"]
                    tradecol.controls.append(ft.Text(line+f' | Exit ₹{t["exit"]:.2f} | P&L ₹{value:,.2f}',size=11,color=GREEN if value>=0 else RED))
            if not trades: tradecol.controls.append(ft.Text("अभी कोई paper trade नहीं है।",color=MUTED))
            body.controls=[ft.Text("Paper Trading",size=19,weight=ft.FontWeight.BOLD),tradecol,
                ft.Text("यह simulation है, कोई वास्तविक order नहीं। App बंद होने पर trades reset हो सकते हैं।",size=10,color=MUTED)]
        elif active=="Alerts":
            body.controls=[ft.Text("Alerts",size=19,weight=ft.FontWeight.BOLD),
                ft.Switch(label="Paper Alerts ON/OFF",value=alerts,on_change=toggle_alert),
                ft.Text("इस संस्करण में switch preference रखता है; push notifications अभी शामिल नहीं हैं।",size=11,color=MUTED)]
        page.update()

    def toggle_alert(e):
        nonlocal alerts
        alerts=e.control.value; render()

    def nav(name):
        nonlocal active
        active=name; render()

    page.add(ft.Column([
        ft.Text("BOT KING",size=24,weight=ft.FontWeight.BOLD,color=GOLD),status,
        ft.Row([ft.TextButton(x,on_click=lambda e,n=x:nav(n)) for x in
                ["Dashboard","Watchlist","Options","Charts","Paper","Alerts"]],wrap=True),
        ft.Divider(color="#34445B"),body
    ],expand=True,scroll=ft.ScrollMode.AUTO))
    render()
    page.run_task(refresh)

ft.app(target=main)
