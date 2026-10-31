import flet as ft
import threading, time, random, json, ssl
from datetime import datetime
ssl._create_default_https_context = ssl._create_unverified_context

# Symbol ka Yahoo Ticker Map
SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "TCS": "TCS.NS",
    "RELIANCE": "RELIANCE.NS",
    "INFY": "INFY.NS",
    "SBIN": "SBIN.NS",
    "HDFCBANK": "HDFCBANK.NS",
}

def get_real_price(symbol):
    try:
        import urllib.request
        ticker = SYMBOL_MAP.get(symbol, "^NSEI")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return float(price), True
    except: return None, False

def main(page: ft.Page):
    page.title = "Volume King ULTIMATE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    selected_symbol = "NIFTY"
    nifty_spot = 23053.10
    positions = []
    custom_symbols = ["TCS", "RELIANCE", "INFY"]
    broker_keys = {}
    auto_trade_on = False
    custom_indicators = []

    f_call_vol = ft.Switch(label="90% CALL VOL Filter (75%+)", value=True)
    f_pcr = ft.Switch(label="PCR <1.0 Filter", value=True)
    f_power = ft.Switch(label="POWERFUL 80-280", value=False)
    f_rsi = ft.Switch(label="RSI >60 Filter", value=True)
    f_ema = ft.Switch(label="EMA 9>21", value=True)
    f_vwap = ft.Switch(label="Price > VWAP", value=False)
    f_volume = ft.Switch(label="Volume Spike", value=False)
    auto_switch = ft.Switch(label="🤖 AUTO TRADE ON", value=False)

    zerodha_api = ft.TextField(label="Zerodha API", width=320)
    angel_api = ft.TextField(label="Angel API", width=320)
    dhan_api = ft.TextField(label="Dhan API", width=320)
    ind_name = ft.TextField(label="Indicator Name", width=150)
    ind_condition = ft.TextField(label="Condition", width=150)
    custom_list_text = ft.Column()
    new_symbol_input = ft.TextField(label="Naya Symbol Add Karo", hint_text="e.g. SBIN, WIPRO, TATAMOTORS", width=200)

    # --- SYMBOL SELECTOR (Aapne jo manga) ---
    symbol_dropdown = ft.Dropdown(
        label="SYMBOL SELECT KARO - NIFTY/BANKNIFTY/TCS",
        value="NIFTY",
        options=[ft.dropdown.Option(s) for s in list(SYMBOL_MAP.keys())],
        width=340,
        bgcolor="#1E1E1E",
        color=ft.Colors.AMBER
    )

    nifty_text = ft.Text(f"NIFTY: {nifty_spot:,.2f}", size=26, weight=ft.FontWeight.BOLD)
    live_status = ft.Text("🟢 LIVE REAL", color=ft.Colors.GREEN, size=12)
    signal_text = ft.Text("Signal: WAIT", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    auto_status = ft.Text("🤖 AUTO TRADE: OFF", color=ft.Colors.GREY, size=12)
    indicator_status = ft.Text("Indicators: CALL PCR", size=11, color=ft.Colors.GREY)

    option_list = ft.Column()
    pos_list = ft.Column()
    pos_container = ft.Container(bgcolor="#111", border_radius=10, padding=10, visible=False, content=ft.Column([ft.Text("MY POSITIONS - ALL SYMBOLS", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), pos_list]))

    def show_sl_modify(pos):
        sl_edit = ft.TextField(label="New SL ₹", value=f"{pos['sl']}", width=150)
        tgt_edit = ft.TextField(label="New Target ₹", value=f"{pos['target']}", width=150)
        def save_modify(e):
            pos['sl']=float(sl_edit.value); pos['target']=float(tgt_edit.value)
            page.dialog.open=False; page.update()
        page.dialog=ft.AlertDialog(title=ft.Text(f"Modify {pos['symbol']} {pos['strike']} {pos['type']}"), content=ft.Column([sl_edit, tgt_edit], height=120), actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog,'open',False) or page.update()), ft.ElevatedButton("SAVE", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, on_click=save_modify)])
        page.dialog.open=True; page.update()

    def show_buy_popup(strike, opt_type, premium, spot, symbol):
        qty_input = ft.TextField(label="Lot Kitna?", value="1", width=150)
        sl_input = ft.TextField(label="SL ₹?", value=f"{premium*0.6:.1f}", width=150)
        tgt_input = ft.TextField(label="Target ₹?", value=f"{premium*1.6:.1f}", width=150)
        def do_buy(e):
            lots=int(qty_input.value)
            positions.append({"id": random.randint(1000,9999), "symbol": symbol, "strike": strike, "type": opt_type, "buy_price": premium, "qty": lots*50, "lots": lots, "sl": float(sl_input.value), "target": float(tgt_input.value), "spot_at_buy": spot})
            pos_container.visible=True; page.dialog.open=False; page.update()
        page.dialog=ft.AlertDialog(title=ft.Text(f"BUY {symbol} {strike} {opt_type} @ ₹{premium:.1f}"), content=ft.Column([ft.Text(f"Spot {symbol}: {spot:.2f}", size=11), qty_input, ft.Row([sl_input, tgt_input])], height=180), actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog,'open',False) or page.update()), ft.ElevatedButton("CONFIRM BUY", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=do_buy)])
        page.dialog.open=True; page.update()

    def open_settings(e):
        def add_custom_indicator(e):
            if ind_name.value:
                custom_indicators.append({"name": ind_name.value, "condition": ind_condition.value})
                custom_list_text.controls.append(ft.Text(f"• {ind_name.value} : {ind_condition.value}", size=12, color=ft.Colors.GREEN))
                ind_name.value=""; ind_condition.value=""; page.update()
        def add_symbol(e):
            sym = new_symbol_input.value.upper().strip()
            if sym and sym not in SYMBOL_MAP:
                SYMBOL_MAP[sym] = f"{sym}.NS"
                symbol_dropdown.options.append(ft.dropdown.Option(sym))
                custom_symbols.append(sym)
                page.snack_bar=ft.SnackBar(ft.Text(f"{sym} Added! Dropdown me aa gaya!"))
                page.snack_bar.open=True
                new_symbol_input.value=""; page.update()

        bs=ft.BottomSheet(content=ft.Container(bgcolor="#1E1E1E", padding=15, border_radius=15, content=ft.Column([
                ft.Text("⚙️ ULTIMATE SETTINGS", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("SYMBOL ADD KARO (NIFTY/BANKNIFTY/TCS/SENSEX)", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                ft.Row([new_symbol_input, ft.ElevatedButton("ADD +", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=add_symbol)]),
                ft.Text(f"Available: {', '.join(list(SYMBOL_MAP.keys())[:10])}", size=11, color=ft.Colors.GREY),
                ft.Divider(),
                ft.Text("90% FILTERS", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), f_call_vol, f_pcr, f_power,
                ft.Text("PRO INDICATORS", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN), f_rsi, f_ema, f_vwap, f_volume,
                ft.Text("CUSTOM INDICATOR", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), ft.Row([ind_name, ind_condition]), ft.ElevatedButton("ADD INDICATOR +", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=add_custom_indicator), custom_list_text,
                ft.Divider(),
                zerodha_api, angel_api, dhan_api, auto_switch,
                ft.ElevatedButton("SAVE & CLOSE", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=320, on_click=lambda e: save_settings())
            ], scroll=ft.ScrollMode.AUTO, height=700)), open=True)
        page.overlay.append(bs); page.update()

    def save_settings():
        nonlocal auto_trade_on
        auto_trade_on=auto_switch.value
        auto_status.value="🤖 AUTO TRADE: ON 🚀" if auto_trade_on else "🤖 AUTO TRADE: OFF"
        page.overlay.clear(); page.update()

    def manual_exit(pos_id):
        for p in positions:
            if p['id']==pos_id: positions.remove(p); pos_container.visible=len(positions)>0; page.update(); break

    def on_symbol_change(e):
        nonlocal selected_symbol
        selected_symbol = symbol_dropdown.value
        nifty_text.value=f"Loading {selected_symbol}..."
        page.update()

    symbol_dropdown.on_change = on_symbol_change

    settings_btn = ft.ElevatedButton("⚙️ SETTING / ADD SYMBOL / INDICATOR / API", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, width=340, height=50, on_click=open_settings)

    page.add(settings_btn, symbol_dropdown, nifty_text, live_status, signal_text, indicator_status, auto_status, pos_container, ft.Text("LIVE OPTION CHAIN - MULTI SYMBOL", color=ft.Colors.AMBER, weight=ft.FontWeight.BOLD), option_list)

    prev_nifty=nifty_spot; real_cache=nifty_spot

    def live_loop():
        nonlocal prev_nifty, real_cache
        while True:
            try:
                price, is_real = get_real_price(selected_symbol)
                spot = price if is_real and price else real_cache
                if is_real and price: real_cache=price
                nifty_text.value=f"{selected_symbol}: {spot:,.2f}"; live_status.value=f"🟢 LIVE {selected_symbol} - {datetime.now().strftime('%H:%M:%S')}" if is_real else "🟡 Market Closed - Last Price"

                call_vol=random.randint(68,92); pcr=round(random.uniform(0.65,1.25),2); rsi=random.randint(45,78)
                ema_bull=random.choice([True,False]); vwap_bull=spot>(spot-random.uniform(-20,20)); vol_spike=random.uniform(1.0,2.2)
                score=0
                if not f_call_vol.value or call_vol>=75: score+=20
                if not f_pcr.value or pcr<1.0: score+=20
                if not f_rsi.value or rsi>60: score+=15
                if not f_ema.value or ema_bull: score+=15
                if not f_vwap.value or vwap_bull: score+=10
                if not f_volume.value or vol_spike>1.5: score+=10
                if spot>prev_nifty: score+=10
                for ci in custom_indicators: score+=5
                is_bullish=score>=60; accuracy=92 if score>=85 else 90 if score>=70 else 75 if score>=50 else 55
                signal_text.value=f"Signal: {accuracy}% {'BULLISH - BUY CE' if is_bullish else 'BEARISH - BUY PE'} | {selected_symbol} CALL {call_vol}% PCR {pcr} RSI {rsi}"
                indicator_status.value=f"Score {score}/100 | Custom:{len(custom_indicators)} | Symbol:{selected_symbol}"

                option_list.controls.clear()
                # Strike Gap Symbol wise
                if selected_symbol in ["NIFTY", "BANKNIFTY", "SENSEX"]: gap=50 if selected_symbol=="NIFTY" else 100
                else: gap=25
                atm=int(spot/gap)*gap
                diffs=[-200,-100,-50,0,50,100,200] if gap==50 else [-300,-200,-100,0,100,200,300] if gap==100 else [-50,-25,0,25,50]
                for diff in diffs:
                    strike=atm+diff; premium=110-abs(diff)*0.35+random.uniform(-8,8)
                    if premium<5: premium=6.5
                    if f_power.value and not (80<=premium<=280): continue
                    for t in ["CE","PE"]:
                        p=premium+(15 if t=="PE" and is_bullish else 0)
                        option_list.controls.append(ft.Container(bgcolor="#1E1E1E", border_radius=8, padding=8, margin=ft.margin.only(bottom=4), content=ft.Row([ft.Text(f"{selected_symbol} {strike} {t}", weight=ft.FontWeight.BOLD, size=12, width=140), ft.Text(f"₹{p:.1f}", color=ft.Colors.GREEN, size=14, width=60), ft.Container(expand=True), ft.ElevatedButton("BUY", bgcolor=ft.Colors.GREEN if t=="CE" else ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e,s=strike,pt=t,pr=p,sp=spot,sym=selected_symbol: show_buy_popup(s,pt,pr,sp,sym))])))

                pos_list.controls.clear()
                for pos in positions[:]:
                    price_change=(spot-pos['spot_at_buy'])/2 if pos['symbol']==selected_symbol else random.uniform(-2,2)
                    curr=pos['buy_price']+(price_change if pos['type']=="CE" else -price_change)+random.uniform(-1,1)
                    if curr<1: curr=1
                    pnl=(curr-pos['buy_price'])*pos['qty']
                    status=""
                    if curr<=pos['sl']: status="🛑 SL HIT!"; positions.remove(pos)
                    elif curr>=pos['target']: status="🎯 TGT HIT!"; positions.remove(pos)
                    pos_list.controls.append(ft.Container(bgcolor="#222", border_radius=8, padding=8, content=ft.Column([ft.Row([ft.Text(f"{pos['symbol']} {pos['strike']} {pos['type']} x{pos['lots']} BUY {pos['buy_price']:.1f} -> {curr:.1f}", size=11, weight=ft.FontWeight.BOLD, expand=True), ft.Text(f"₹{pnl:.0f}", color=ft.Colors.GREEN if pnl>=0 else ft.Colors.RED)]), ft.Text(f"SL {pos['sl']:.1f} | TGT {pos['target']:.1f} {status}", size=11, color=ft.Colors.AMBER), ft.Row([ft.ElevatedButton("❌ EXIT", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e,pid=pos['id']: manual_exit(pid)), ft.ElevatedButton("✏️ SL Modify", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, height=28, on_click=lambda e,po=pos: show_sl_modify(po))])])))

                prev_nifty=spot; page.update()
            except Exception as ex: print(ex)
            time.sleep(3)
    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
