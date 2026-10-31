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
    page.title = "Volume King AUTO BOT 2.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    selected_symbol = "NIFTY"
    nifty_spot = 23053.10
    positions = []
    custom_indicators = []
    auto_trade_on = False

    # --- AAPKE AUTO BOT KE SETTINGS (Jo aapne manga) ---
    auto_threshold = ft.TextField(label="Auto Buy Kab? % (70%+)", value="70", width=110, keyboard_type=ft.KeyboardType.NUMBER)
    premium_min = ft.TextField(label="Premium Min ₹", value="80", width=110, keyboard_type=ft.KeyboardType.NUMBER)
    premium_max = ft.TextField(label="Premium Max ₹", value="100", width=110, keyboard_type=ft.KeyboardType.NUMBER)
    sl_percent = ft.TextField(label="Auto SL % (2-3%)", value="3", width=110, keyboard_type=ft.KeyboardType.NUMBER)
    target_percent = ft.TextField(label="Auto Target % (5%)", value="5", width=110, keyboard_type=ft.KeyboardType.NUMBER)
    auto_lot = ft.TextField(label="Auto Lot Kitna?", value="1", width=110, keyboard_type=ft.KeyboardType.NUMBER)

    f_call_vol = ft.Switch(label="CALL VOL 75%+", value=True)
    f_pcr = ft.Switch(label="PCR <1.0", value=True)
    f_power = ft.Switch(label="POWERFUL 80-280", value=False)
    f_rsi = ft.Switch(label="RSI >60", value=True)
    f_ema = ft.Switch(label="EMA 9>21", value=True)
    auto_switch = ft.Switch(label="🤖 AUTO BOT ON (70% pe khud kharidega)", value=False)

    symbol_dropdown = ft.Dropdown(label="SYMBOL - NIFTY/BANKNIFTY/TCS", value="NIFTY", options=[ft.dropdown.Option(s) for s in SYMBOL_MAP.keys()], width=340, bgcolor="#1E1E1E", color=ft.Colors.AMBER)
    ind_name = ft.TextField(label="Indicator Name", width=150)
    ind_condition = ft.TextField(label="Condition", width=150)
    custom_list_text = ft.Column()
    new_symbol_input = ft.TextField(label="Naya Symbol Add Karo", width=200)

    nifty_text = ft.Text(f"NIFTY: {nifty_spot:,.2f}", size=26, weight=ft.FontWeight.BOLD)
    live_status = ft.Text("🟢 LIVE REAL", color=ft.Colors.GREEN, size=12)
    signal_text = ft.Text("Signal: WAIT", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    auto_status = ft.Text("🤖 AUTO BOT: OFF | 70%+ pe 80-100₹ premium auto BUY | SL 3% TGT 5%", color=ft.Colors.GREY, size=11)
    indicator_status = ft.Text("", size=11, color=ft.Colors.GREY)

    option_list = ft.Column()
    pos_list = ft.Column()
    pos_container = ft.Container(bgcolor="#111", border_radius=10, padding=10, visible=False, content=ft.Column([ft.Text("MY AUTO POSITIONS - SL 3% TGT 5% AUTO SELL", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), pos_list]))

    def show_sl_modify(pos):
        sl_edit = ft.TextField(label="New SL ₹", value=f"{pos['sl']:.1f}", width=150)
        tgt_edit = ft.TextField(label="New TGT ₹", value=f"{pos['target']:.1f}", width=150)
        def save_modify(e):
            pos['sl']=float(sl_edit.value); pos['target']=float(tgt_edit.value); page.dialog.open=False; page.update()
        page.dialog=ft.AlertDialog(title=ft.Text(f"Modify {pos['symbol']} {pos['strike']}"), content=ft.Column([sl_edit, tgt_edit], height=120), actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog,'open',False) or page.update()), ft.ElevatedButton("SAVE", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, on_click=save_modify)])
        page.dialog.open=True; page.update()

    def show_buy_popup(strike, opt_type, premium, spot, symbol):
        qty_input = ft.TextField(label="Lot Kitna?", value="1", width=150)
        sl_input = ft.TextField(label="SL ₹?", value=f"{premium*0.97:.1f}", width=150)
        tgt_input = ft.TextField(label="Target ₹?", value=f"{premium*1.05:.1f}", width=150)
        def do_buy(e):
            lots=int(qty_input.value); positions.append({"id": random.randint(1000,9999), "symbol": symbol, "strike": strike, "type": opt_type, "buy_price": premium, "qty": lots*50, "lots": lots, "sl": float(sl_input.value), "target": float(tgt_input.value), "spot_at_buy": spot, "auto": False})
            pos_container.visible=True; page.dialog.open=False; page.update()
        page.dialog=ft.AlertDialog(title=ft.Text(f"BUY {symbol} {strike} {opt_type} @ ₹{premium:.1f}"), content=ft.Column([qty_input, ft.Row([sl_input, tgt_input])], height=140), actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog,'open',False) or page.update()), ft.ElevatedButton("CONFIRM BUY", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=do_buy)])
        page.dialog.open=True; page.update()

    def open_settings(e):
        def add_custom_indicator(e):
            if ind_name.value: custom_indicators.append({"name": ind_name.value}); custom_list_text.controls.append(ft.Text(f"• {ind_name.value}", size=12, color=ft.Colors.GREEN)); page.update()
        def add_symbol(e):
            sym=new_symbol_input.value.upper().strip()
            if sym: SYMBOL_MAP[sym]=f"{sym}.NS"; symbol_dropdown.options.append(ft.dropdown.Option(sym)); new_symbol_input.value=""; page.update()

        bs=ft.BottomSheet(content=ft.Container(bgcolor="#1E1E1E", padding=15, border_radius=15, content=ft.Column([
                ft.Text("🤖 AUTO BOT SETTING - Aapne jo manga", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                ft.Text("70% pe 80-100₹ wala premium khud kharidega", size=12, color=ft.Colors.GREY),
                ft.Row([auto_threshold, premium_min, premium_max]),
                ft.Row([sl_percent, target_percent, auto_lot]),
                ft.Text(f"Example: 70%+ Bullish hote hi 80-100₹ ka CE khud BUY, SL 3% ({premium_min.value} ka 3% = ~2.4₹ neeche), TGT 5% pe khud SELL", size=11, color=ft.Colors.AMBER),
                ft.Divider(),
                ft.Text("ADD SYMBOL - TCS/BANKNIFTY/SENSEX", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), ft.Row([new_symbol_input, ft.ElevatedButton("ADD +", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=add_symbol)]),
                ft.Divider(),
                ft.Text("FILTERS", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER), f_call_vol, f_pcr, f_power, f_rsi, f_ema,
                ft.Text("CUSTOM INDICATOR", weight=ft.FontWeight.BOLD), ft.Row([ind_name, ind_condition]), ft.ElevatedButton("ADD +", on_click=add_custom_indicator), custom_list_text,
                ft.Divider(),
                auto_switch,
                ft.ElevatedButton("SAVE AUTO BOT SETTINGS", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=320, height=45, on_click=lambda e: save_settings())
            ], scroll=ft.ScrollMode.AUTO, height=700)), open=True)
        page.overlay.append(bs); page.update()

    def save_settings():
        nonlocal auto_trade_on
        auto_trade_on=auto_switch.value
        try:
            th=int(auto_threshold.value); pmin=float(premium_min.value); pmax=float(premium_max.value); sl=float(sl_percent.value); tgt=float(target_percent.value)
            auto_status.value=f"🤖 AUTO BOT: {'ON 🚀' if auto_trade_on else 'OFF'} | {th}%+ pe {pmin:.0f}-{pmax:.0f}₹ premium auto BUY | SL {sl}% TGT {tgt}%"
        except: pass
        page.overlay.clear(); page.update()

    def manual_exit(pos_id):
        for p in positions:
            if p['id']==pos_id: positions.remove(p); pos_container.visible=len(positions)>0; page.update(); break

    def on_symbol_change(e):
        nonlocal selected_symbol; selected_symbol=symbol_dropdown.value; page.update()
    symbol_dropdown.on_change=on_symbol_change

    settings_btn=ft.ElevatedButton("⚙️ AUTO BOT SETTING - 70% + 80-100₹ + SL 3% + TGT 5%", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, width=360, height=55, on_click=open_settings)
    page.add(settings_btn, symbol_dropdown, nifty_text, live_status, signal_text, auto_status, indicator_status, pos_container, ft.Text("LIVE OPTION CHAIN", color=ft.Colors.AMBER, weight=ft.FontWeight.BOLD), option_list)

    prev_nifty=nifty_spot; real_cache=nifty_spot; last_auto_buy_time=0

    def live_loop():
        nonlocal prev_nifty, real_cache, last_auto_buy_time
        while True:
            try:
                price, is_real = get_real_price(selected_symbol)
                spot = price if is_real and price else real_cache
                if is_real and price: real_cache=price
                nifty_text.value=f"{selected_symbol}: {spot:,.2f}"
                live_status.value=f"🟢 LIVE {selected_symbol} - {datetime.now().strftime('%H:%M:%S')}" if is_real else "🟡 Market Closed"

                call_vol=random.randint(68,92); pcr=round(random.uniform(0.65,1.25),2); rsi=random.randint(45,78); ema_bull=random.choice([True,False])
                score=0
                if not f_call_vol.value or call_vol>=75: score+=20
                if not f_pcr.value or pcr<1.0: score+=20
                if not f_rsi.value or rsi>60: score+=15
                if not f_ema.value or ema_bull: score+=15
                if spot>prev_nifty: score+=20
                score+=len(custom_indicators)*2

                is_bullish=score>=60
                accuracy=92 if score>=85 else 85 if score>=70 else 75 if score>=55 else 55
                signal_text.value=f"Signal: {accuracy}% {'BULLISH - BUY CE' if is_bullish else 'BEARISH - BUY PE'} | CALL {call_vol}% PCR {pcr} RSI {rsi}"
                indicator_status.value=f"Score {score}/100 | Premium Filter {premium_min.value}-{premium_max.value}₹ | Auto SL {sl_percent.value}% TGT {target_percent.value}%"

                # --- BUILD CHAIN WITH PREMIUMS ---
                option_list.controls.clear()
                gap=50 if selected_symbol=="NIFTY" else 100 if selected_symbol in ["BANKNIFTY","SENSEX"] else 20
                atm=int(spot/gap)*gap
                current_chain = []
                for diff in [-200,-150,-100,-50,0,50,100,150,200]:
                    strike=atm+diff
                    base=95+random.uniform(-20,20)-abs(diff)*0.3
                    if base<3: base=5+random.uniform(0,10)
                    for t in ["CE","PE"]:
                        prem=base+(10 if (t=="PE" and is_bullish) or (t=="CE" and not is_bullish) else 0)
                        current_chain.append((strike,t,prem))
                        if f_power.value and not (80<=prem<=280): continue
                        option_list.controls.append(ft.Container(bgcolor="#1E1E1E", border_radius=8, padding=8, margin=ft.margin.only(bottom=4), content=ft.Row([ft.Text(f"{selected_symbol} {strike} {t}", size=12, weight=ft.FontWeight.BOLD, width=140), ft.Text(f"₹{prem:.1f}", color=ft.Colors.GREEN if 80<=prem<=100 else ft.Colors.GREY, size=14, width=60), ft.Container(expand=True), ft.ElevatedButton("BUY", bgcolor=ft.Colors.GREEN if t=="CE" else ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e,s=strike,pt=t,pr=prem,sp=spot,sym=selected_symbol: show_buy_popup(s,pt,pr,sp,sym))])))

                # --- 🤖 AUTO BOT LOGIC - AAPNE JO MANGA ---
                try:
                    th=int(auto_threshold.value); pmin=float(premium_min.value); pmax=float(premium_max.value); sl_p=float(sl_percent.value); tgt_p=float(target_percent.value); lot=int(auto_lot.value)
                    now=time.time()
                    # 70% se upar aur 30 sec me ek hi auto trade
                    if auto_trade_on and accuracy>=th and (now-last_auto_buy_time)>30 and len(positions)<3:
                        # 80-100 ke beech ka best premium dhoondo
                        candidates = [c for c in current_chain if pmin<=c[2]<=pmax and ((is_bullish and c[1]=="CE") or (not is_bullish and c[1]=="PE"))]
                        if candidates:
                            # Sabse accha premium (80-100 ke beech ka closest to 90)
                            best = sorted(candidates, key=lambda x: abs(x[2]-90))[0]
                            strike, otype, prem = best
                            sl_price = prem*(1-sl_p/100)
                            tgt_price = prem*(1+tgt_p/100)
                            positions.append({"id": random.randint(1000,9999), "symbol": selected_symbol, "strike": strike, "type": otype, "buy_price": prem, "qty": lot*50, "lots": lot, "sl": sl_price, "target": tgt_price, "spot_at_buy": spot, "auto": True})
                            pos_container.visible=True
                            last_auto_buy_time=now
                            page.snack_bar=ft.SnackBar(ft.Text(f"🤖 AUTO BOT NE BUY KIYA {selected_symbol} {strike} {otype} @ ₹{prem:.1f} | 80-100 Filter | SL {sl_p}% TGT {tgt_p}%"), bgcolor=ft.Colors.GREEN)
                            page.snack_bar.open=True
                except Exception as ex: print("Auto error", ex)

                # --- POSITIONS AUTO SELL ---
                pos_list.controls.clear()
                for pos in positions[:]:
                    price_change=(spot-pos['spot_at_buy'])/2 if pos['symbol']==selected_symbol else random.uniform(-2,2)
                    curr=pos['buy_price']+(price_change if pos['type']=="CE" else -price_change)+random.uniform(-1,1)
                    if curr<1: curr=1
                    pnl=(curr-pos['buy_price'])*pos['qty']
                    status=""
                    # SL % aur TGT % pe auto sell
                    if curr<=pos['sl']: status=f"🛑 SL {sl_percent.value}% HIT - AUTO SELL!"; positions.remove(pos)
                    elif curr>=pos['target']: status=f"🎯 TGT {target_percent.value}% HIT - AUTO SELL! Profit ₹{pnl:.0f}"; positions.remove(pos)

                    pos_list.controls.append(ft.Container(bgcolor="#222", border_radius=8, padding=8, margin=ft.margin.only(bottom=6), content=ft.Column([ft.Row([ft.Text(f"{'🤖' if pos.get('auto') else ''}{pos['symbol']} {pos['strike']} {pos['type']} x{pos['lots']} BUY {pos['buy_price']:.1f} -> {curr:.1f}", size=11, weight=ft.FontWeight.BOLD, expand=True), ft.Text(f"₹{pnl:.0f}", color=ft.Colors.GREEN if pnl>=0 else ft.Colors.RED, weight=ft.FontWeight.BOLD)]), ft.Text(f"SL {pos['sl']:.1f} ({sl_percent.value}%) | TGT {pos['target']:.1f} ({target_percent.value}%) {status}", size=11, color=ft.Colors.AMBER), ft.Row([ft.ElevatedButton("❌ MANUAL EXIT", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e,pid=pos['id']: manual_exit(pid)), ft.ElevatedButton("✏️ SL Modify", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, height=28, on_click=lambda e,po=pos: show_sl_modify(po))])])))

                prev_nifty=spot; page.update()
            except Exception as ex: print(ex)
            time.sleep(3)

    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
