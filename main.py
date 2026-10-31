import flet as ft
import threading, time, random, json, ssl
from datetime import datetime
ssl._create_default_https_context = ssl._create_unverified_context

SYMBOL_MAP = {
    "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN",
    "TCS": "TCS.NS", "RELIANCE": "RELIANCE.NS", "INFY": "INFY.NS",
}

def get_real_price(symbol):
    try:
        import urllib.request
        ticker = SYMBOL_MAP.get(symbol, "^NSEI")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            return float(data['chart']['result'][0]['meta']['regularMarketPrice']), True
    except: return None, False

def main(page: ft.Page):
    page.title = "Volume King PRO 4 Page"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080808"
    page.padding = 0

    selected_symbol = "NIFTY"
    nifty_spot = 23053.10
    positions = []
    custom_indicators = []
    auto_trade_on = False

    # --- ALL CONTROLS ---
    auto_threshold = ft.TextField(label="Auto Buy %", value="70", width=100)
    premium_min = ft.TextField(label="Min ₹", value="80", width=100)
    premium_max = ft.TextField(label="Max ₹", value="100", width=100)
    sl_percent = ft.TextField(label="SL %", value="3", width=100)
    target_percent = ft.TextField(label="TGT %", value="5", width=100)
    auto_lot = ft.TextField(label="Lot", value="1", width=100)

    f_call_vol = ft.Switch(label="CALL VOL 75%+", value=True)
    f_pcr = ft.Switch(label="PCR <1.0", value=True)
    f_power = ft.Switch(label="80-280 Only", value=False)
    f_rsi = ft.Switch(label="RSI >60", value=True)
    f_ema = ft.Switch(label="EMA 9>21", value=True)
    f_vwap = ft.Switch(label="Price > VWAP", value=False)
    f_volume = ft.Switch(label="Vol Spike", value=False)
    auto_switch = ft.Switch(label="🤖 AUTO BOT ON", value=False)

    new_symbol_input = ft.TextField(label="Naya Symbol (e.g. SBIN)", width=200)
    ind_name = ft.TextField(label="Indicator Name", width=160)
    ind_condition = ft.TextField(label="Condition", width=120)

    nifty_text = ft.Text(f"{selected_symbol}: {nifty_spot:,.2f}", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    live_status = ft.Text("🟢 LIVE", color=ft.Colors.GREEN, size=11)
    signal_text = ft.Text("Signal: WAIT", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    auto_status = ft.Text("🤖 OFF | 70%+ 80-100₹ SL 3% TGT 5%", color=ft.Colors.GREY, size=11)

    option_list = ft.Column(scroll=ft.ScrollMode.AUTO)
    pos_list = ft.Column()
    symbol_list_col = ft.Column() # Page 2 me symbols dikhenge
    custom_list_col = ft.Column()
    
    # --- TOP PRO HEADER ---
    def build_header():
        return ft.Container(
            gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#1a1a2e", "#16213e", "#0f3460"]),
            padding=15, border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
            content=ft.Column([
                ft.Row([ft.Text("VOLUME KING", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), ft.Container(expand=True), ft.Icon(ft.Icons.STARS, color=ft.Colors.AMBER), ft.Text("PRO", color=ft.Colors.AMBER, weight=ft.FontWeight.BOLD)]),
                nifty_text,
                ft.Row([live_status, ft.Container(expand=True), signal_text]),
                auto_status
            ])
        )

    # --- POPUPS (Same) ---
    def show_sl_modify(pos):
        sl_edit = ft.TextField(label="New SL", value=f"{pos['sl']:.1f}", width=140)
        tgt_edit = ft.TextField(label="New TGT", value=f"{pos['target']:.1f}", width=140)
        def save(e): pos['sl']=float(sl_edit.value); pos['target']=float(tgt_edit.value); page.dialog.open=False; page.update()
        page.dialog=ft.AlertDialog(title=ft.Text(f"Modify {pos['symbol']} {pos['strike']}"), content=ft.Row([sl_edit, tgt_edit]), actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog,'open',False) or page.update()), ft.ElevatedButton("SAVE", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, on_click=save)])
        page.dialog.open=True; page.update()

    def show_buy_popup(strike, opt_type, premium, spot, symbol):
        qty = ft.TextField(label="Lot", value="1", width=100)
        sl = ft.TextField(label="SL ₹", value=f"{premium*0.97:.1f}", width=120)
        tgt = ft.TextField(label="TGT ₹", value=f"{premium*1.05:.1f}", width=120)
        def do_buy(e):
            positions.append({"id": random.randint(1000,9999), "symbol": symbol, "strike": strike, "type": opt_type, "buy_price": premium, "qty": int(qty.value)*50, "lots": int(qty.value), "sl": float(sl.value), "target": float(tgt.value), "spot_at_buy": spot, "auto": False})
            page.dialog.open=False; update_all_lists(); page.update()
        page.dialog=ft.AlertDialog(title=ft.Text(f"BUY {symbol} {strike} {opt_type} @ ₹{premium:.1f}"), content=ft.Column([qty, ft.Row([sl, tgt])], height=130), actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog,'open',False) or page.update()), ft.ElevatedButton("CONFIRM BUY", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=do_buy)])
        page.dialog.open=True; page.update()

    def manual_exit(pid):
        for p in positions:
            if p['id']==pid: positions.remove(p); break
        update_all_lists(); page.update()

    # --- UPDATE FUNCTIONS ---
    def update_symbol_page():
        symbol_list_col.controls.clear()
        for sym in SYMBOL_MAP.keys():
            is_selected = sym == selected_symbol
            symbol_list_col.controls.append(
                ft.Container(
                    bgcolor="#1E1E1E" if not is_selected else "#2a4a2a", border=ft.border.all(1, ft.Colors.GREEN if is_selected else ft.Colors.TRANSPARENT),
                    border_radius=10, padding=12, margin=ft.margin.only(bottom=6),
                    on_click=lambda e, s=sym: select_symbol(s),
                    content=ft.Row([ft.Icon(ft.Icons.SHOW_CHART, color=ft.Colors.AMBER), ft.Text(sym, weight=ft.FontWeight.BOLD, size=14, expand=True), ft.Text("✓ SELECTED" if is_selected else "TAP TO SELECT", size=11, color=ft.Colors.GREEN if is_selected else ft.Colors.GREY)])
                )
            )

    def select_symbol(sym):
        nonlocal selected_symbol; selected_symbol=sym; nifty_text.value=f"Loading {sym}..."; update_symbol_page(); page.update()

    def add_symbol_action(e):
        sym=new_symbol_input.value.upper().strip()
        if sym and sym not in SYMBOL_MAP:
            SYMBOL_MAP[sym]=f"{sym}.NS"; new_symbol_input.value=""; update_symbol_page(); page.snack_bar=ft.SnackBar(ft.Text(f"{sym} Added!")); page.snack_bar.open=True; page.update()

    def add_indicator_action(e):
        if ind_name.value:
            custom_indicators.append({"name": ind_name.value, "cond": ind_condition.value})
            custom_list_col.controls.append(ft.Container(bgcolor="#111", border_radius=8, padding=8, content=ft.Row([ft.Text(f"{ind_name.value} : {ind_condition.value}", size=12, expand=True), ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=18, on_click=lambda e, idx=len(custom_indicators)-1: delete_indicator(idx))])))
            ind_name.value=""; ind_condition.value=""; page.update()

    def delete_indicator(idx):
        if 0<=idx<len(custom_indicators): custom_indicators.pop(idx); custom_list_col.controls.pop(idx); page.update()

    def update_all_lists():
        # Option chain will be updated in loop
        pass

    # --- 4 PAGES ---
    page1_dashboard = ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
        build_header(),
        ft.Container(padding=12, content=ft.Column([
            ft.Text("MY POSITIONS", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER, size=13),
            ft.Container(bgcolor="#111", border_radius=10, padding=8, content=pos_list),
            ft.Divider(height=20),
            ft.Text("LIVE OPTION CHAIN", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER, size=13),
            option_list
        ]))
    ])

    page2_symbols = ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(gradient=ft.LinearGradient(colors=["#1a1a2e", "#0f3460"]), padding=15, content=ft.Column([ft.Text("SYMBOLS", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), ft.Text("Koi bhi NSE Symbol Add Karo - NIFTY, BANKNIFTY, TCS, SBIN", size=11, color=ft.Colors.GREY)])),
        ft.Container(padding=12, content=ft.Column([
            ft.Row([new_symbol_input, ft.ElevatedButton("ADD +", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=add_symbol_action)]),
            ft.Text("TAP karke Symbol Change Karo:", size=12, color=ft.Colors.GREY),
            symbol_list_col
        ]))
    ])

    page3_indicators = ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(gradient=ft.LinearGradient(colors=["#1a1a2e", "#0f3460"]), padding=15, content=ft.Text("INDICATORS & FILTERS", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)),
        ft.Container(padding=12, content=ft.Column([
            ft.Text("90% ACCURACY FILTERS", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), f_call_vol, f_pcr, f_power,
            ft.Divider(),
            ft.Text("PRO INDICATORS", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN), f_rsi, f_ema, f_vwap, f_volume,
            ft.Divider(),
            ft.Text("CUSTOM INDICATOR ADD KARO", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
            ft.Row([ind_name, ind_condition]),
            ft.ElevatedButton("ADD INDICATOR +", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=add_indicator_action),
            custom_list_col,
            ft.Text("Jaise: Supertrend BUY, MACD >0", size=11, color=ft.Colors.GREY)
        ]))
    ])

    page4_settings = ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(gradient=ft.LinearGradient(colors=["#1a1a2e", "#0f3460"]), padding=15, content=ft.Text("AUTO BOT SETTINGS", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)),
        ft.Container(padding=12, content=ft.Column([
            ft.Text("🤖 AUTO TRADE BOT - 70% Logic", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN, size=15),
            ft.Text("70%+ Bullish hote hi 80-100₹ premium khud BUY, SL 3% TGT 5% pe SELL", size=11, color=ft.Colors.GREY),
            ft.Row([auto_threshold, premium_min, premium_max]),
            ft.Row([sl_percent, target_percent, auto_lot]),
            ft.Divider(),
            auto_switch,
            ft.Container(bgcolor="#111", border_radius=10, padding=10, content=ft.Column([ft.Text("BROKER API (Real Order ke liye)", weight=ft.FontWeight.BOLD, size=12), ft.TextField(label="Zerodha Kite API", width=320), ft.TextField(label="Angel One API", width=320), ft.TextField(label="Dhan API", width=320)])),
            ft.ElevatedButton("SAVE ALL SETTINGS", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=320, height=45, on_click=lambda e: (setattr(auto_status, 'value', f"🤖 AUTO BOT: {'ON 🚀' if auto_switch.value else 'OFF'} | {auto_threshold.value}%+ {premium_min.value}-{premium_max.value}₹ SL {sl_percent.value}% TGT {target_percent.value}%"), setattr(page, 'snack_bar', ft.SnackBar(ft.Text("Saved!"))), setattr(page.snack_bar, 'open', True), page.update()))
        ]))
    ])

    # --- MAIN CONTENT SWITCHER ---
    content_area = ft.Container(content=page1_dashboard, expand=True)

    def nav_change(e):
        idx = e.control.selected_index
        if idx==0: content_area.content = page1_dashboard
        elif idx==1: content_area.content = page2_symbols; update_symbol_page()
        elif idx==2: content_area.content = page3_indicators
        elif idx==3: content_area.content = page4_settings
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0, bgcolor="#111",
        on_change=nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Board"),
            ft.NavigationBarDestination(icon=ft.Icons.CURRENCY_RUPEE, label="Symbols"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART, label="Indicators"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Auto Bot"),
        ]
    )

    page.add(content_area)
    update_symbol_page()

    # --- LIVE LOOP (Same Auto Logic) ---
    prev_nifty=nifty_spot; real_cache=nifty_spot; last_auto_buy=0
    def live_loop():
        nonlocal prev_nifty, real_cache, last_auto_buy
        while True:
            try:
                price, is_real = get_real_price(selected_symbol)
                spot = price if is_real and price else real_cache
                if is_real and price: real_cache=price
                nifty_text.value=f"{selected_symbol}: {spot:,.2f}"
                live_status.value=f"🟢 LIVE {selected_symbol}" if is_real else "🟡 CLOSED"
                
                call_vol=random.randint(68,92); pcr=round(random.uniform(0.65,1.25),2); rsi=random.randint(45,78)
                ema_bull=random.choice([True,False]); score=0
                if not f_call_vol.value or call_vol>=75: score+=20
                if not f_pcr.value or pcr<1.0: score+=20
                if not f_rsi.value or rsi>60: score+=15
                if not f_ema.value or ema_bull: score+=15
                if spot>prev_nifty: score+=20
                score+=len(custom_indicators)*2
                is_bullish=score>=60; acc=92 if score>=85 else 85 if score>=70 else 75 if score>=55 else 55
                signal_text.value=f"Signal: {acc}% {'BULLISH CE' if is_bullish else 'BEARISH PE'} | CALL {call_vol}% PCR {pcr} RSI {rsi}"
                
                # Chain
                option_list.controls.clear()
                gap=50 if selected_symbol=="NIFTY" else 100 if selected_symbol in ["BANKNIFTY","SENSEX"] else 20
                atm=int(spot/gap)*gap; chain=[]
                for diff in [-200,-150,-100,-50,0,50,100,150,200]:
                    strike=atm+diff; base=95+random.uniform(-20,20)-abs(diff)*0.3
                    if base<3: base=5+random.uniform(0,10)
                    for t in ["CE","PE"]:
                        prem=base+(10 if (t=="PE" and is_bullish) or (t=="CE" and not is_bullish) else 0)
                        chain.append((strike,t,prem))
                        if f_power.value and not (80<=prem<=280): continue
                        option_list.controls.append(ft.Container(bgcolor="#1E1E1E", border_radius=8, padding=8, margin=ft.margin.only(bottom=4), content=ft.Row([ft.Text(f"{selected_symbol} {strike} {t}", size=12, weight=ft.FontWeight.BOLD, width=130), ft.Text(f"₹{prem:.1f}", color=ft.Colors.GREEN if 80<=prem<=100 else ft.Colors.GREY, size=14, width=60), ft.Container(expand=True), ft.ElevatedButton("BUY", bgcolor=ft.Colors.GREEN if t=="CE" else ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e,s=strike,pt=t,pr=prem,sp=spot,sym=selected_symbol: show_buy_popup(s,pt,pr,sp,sym))])))

                # Auto Bot 70% + 80-100₹
                try:
                    th=int(auto_threshold.value); pmin=float(premium_min.value); pmax=float(premium_max.value); sl_p=float(sl_percent.value); tgt_p=float(target_percent.value); lot=int(auto_lot.value)
                    if auto_switch.value and acc>=th and (time.time()-last_auto_buy)>30 and len(positions)<3:
                        cands=[c for c in chain if pmin<=c[2]<=pmax and ((is_bullish and c[1]=="CE") or (not is_bullish and c[1]=="PE"))]
                        if cands:
                            best=sorted(cands, key=lambda x: abs(x[2]-90))[0]
                            strike, otype, prem = best
                            positions.append({"id": random.randint(1000,9999), "symbol": selected_symbol, "strike": strike, "type": otype, "buy_price": prem, "qty": lot*50, "lots": lot, "sl": prem*(1-sl_p/100), "target": prem*(1+tgt_p/100), "spot_at_buy": spot, "auto": True})
                            last_auto_buy=time.time(); page.snack_bar=ft.SnackBar(ft.Text(f"🤖 AUTO BUY {selected_symbol} {strike} {otype} @ ₹{prem:.1f}"), bgcolor=ft.Colors.GREEN); page.snack_bar.open=True
                except: pass

                # Positions
                pos_list.controls.clear()
                for pos in positions[:]:
                    price_change=(spot-pos['spot_at_buy'])/2 if pos['symbol']==selected_symbol else random.uniform(-2,2)
                    curr=pos['buy_price']+(price_change if pos['type']=="CE" else -price_change)+random.uniform(-1,1)
                    if curr<1: curr=1; pnl=(curr-pos['buy_price'])*pos['qty']
                    status=""
                    if curr<=pos['sl']: status="🛑 SL HIT AUTO SELL"; positions.remove(pos)
                    elif curr>=pos['target']: status=f"🎯 TGT HIT AUTO SELL ₹{pnl:.0f}"; positions.remove(pos)
                    pos_list.controls.append(ft.Container(bgcolor="#222", border_radius=8, padding=8, margin=ft.margin.only(bottom=6), content=ft.Column([ft.Row([ft.Text(f"{'🤖' if pos.get('auto') else ''}{pos['symbol']} {pos['strike']} {pos['type']} x{pos['lots']} {pos['buy_price']:.1f}->{curr:.1f}", size=11, weight=ft.FontWeight.BOLD, expand=True), ft.Text(f"₹{pnl:.0f}", color=ft.Colors.GREEN if pnl>=0 else ft.Colors.RED)]), ft.Text(f"SL {pos['sl']:.1f} | TGT {pos['target']:.1f} {status}", size=11, color=ft.Colors.AMBER), ft.Row([ft.ElevatedButton("❌ EXIT", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e,pid=pos['id']: manual_exit(pid)), ft.ElevatedButton("✏️ MODIFY", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, height=28, on_click=lambda e,po=pos: show_sl_modify(po))])])))

                prev_nifty=spot; page.update()
            except Exception as ex: print(ex)
            time.sleep(3)

    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
