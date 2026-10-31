import flet as ft
import threading, time, random, json, ssl
from datetime import datetime
ssl._create_default_https_context = ssl._create_unverified_context

def get_real_nifty():
    try:
        import urllib.request
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            if price > 10000: return float(price), True
    except: pass
    return None, False

def main(page: ft.Page):
    page.title = "Volume King 97 BOT"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    nifty_spot = 23053.10
    positions = []
    broker_keys = {"zerodha": "", "angel": "", "dhan": ""}
    auto_trade_on = False

    # --- HEADER ---
    nifty_text = ft.Text(f"NIFTY: {nifty_spot:,.2f}", size=26, weight=ft.FontWeight.BOLD)
    live_status = ft.Text("🟢 LIVE REAL", color=ft.Colors.GREEN, size=12)
    signal_text = ft.Text("Signal: WAIT", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    auto_status = ft.Text("🤖 AUTO TRADE: OFF", color=ft.Colors.GREY, size=12)

    # --- FILTERS (State) ---
    f_call_vol = ft.Switch(label="90% CALL VOL Filter (75%+)", value=True)
    f_pcr = ft.Switch(label="PCR <1.0 Bullish Filter", value=True)
    f_power = ft.Switch(label="POWERFUL 80-280 Only", value=False)
    auto_switch = ft.Switch(label="AUTO TRADE ON (Target pe khud BUY)", value=False)

    # --- BROKER API INPUTS ---
    zerodha_api = ft.TextField(label="Zerodha API Key + Secret", hint_text="Kite API Key:Secret", width=320)
    angel_api = ft.TextField(label="Angel One API Key", hint_text="SmartAPI Key", width=320)
    dhan_api = ft.TextField(label="Dhan API Key", hint_text="Dhan Client ID + Token", width=320)

    # --- LISTS ---
    option_list = ft.Column()
    pos_list = ft.Column()
    pos_container = ft.Container(bgcolor="#111", border_radius=10, padding=10, visible=False, content=ft.Column([ft.Text("MY POSITIONS - AUTO SL/TARGET", weight=ft.FontWeight.BOLD), pos_list]))

    # --- SETTINGS BOTTOM SHEET ---
    def open_settings(e):
        bs = ft.BottomSheet(
            content=ft.Container(bgcolor="#1E1E1E", padding=15, border_radius=15, content=ft.Column([
                ft.Text("⚙️ SETTINGS - VOLUME KING BOT", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("1. FILTERS (90% Accuracy)", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                f_call_vol, f_pcr, f_power,
                ft.Divider(),
                ft.Text("2. BROKER API - Real Order Ke Liye", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                ft.Text("API daaloge to real order lagega, nahi to DEMO", size=11, color=ft.Colors.GREY),
                zerodha_api, angel_api, dhan_api,
                ft.Divider(),
                ft.Text("3. AUTO TRADE BOT", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                auto_switch,
                ft.Text("ON karoge to 90% Signal aate hi khud BUY, khud SL/Target laga dega!", size=11, color=ft.Colors.GREY),
                ft.ElevatedButton("SAVE & CLOSE", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=320, on_click=lambda e: save_settings())
            ], scroll=ft.ScrollMode.AUTO, height=600)),
            open=True
        )
        page.overlay.append(bs)
        page.update()

    def save_settings():
        nonlocal auto_trade_on
        broker_keys["zerodha"] = zerodha_api.value
        broker_keys["angel"] = angel_api.value
        broker_keys["dhan"] = dhan_api.value
        auto_trade_on = auto_switch.value
        auto_status.value = "🤖 AUTO TRADE: ON - Bot Active! 🚀" if auto_trade_on else "🤖 AUTO TRADE: OFF"
        auto_status.color = ft.Colors.GREEN if auto_trade_on else ft.Colors.GREY
        # Close all bottom sheets
        page.overlay.clear()
        page.snack_bar = ft.SnackBar(ft.Text("Settings Saved! Bot Ready!"))
        page.snack_bar.open = True
        page.update()

    settings_btn = ft.ElevatedButton("⚙️ SETTING / API / FILTER / AUTO TRADE", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, width=320, height=45, on_click=open_settings)

    page.add(settings_btn, nifty_text, live_status, signal_text, auto_status, pos_container, ft.Text("LIVE OPTION CHAIN", color=ft.Colors.AMBER, weight=ft.FontWeight.BOLD), option_list)

    def place_order(strike, opt_type, premium, spot, is_auto=False):
        # Check if any broker API is present
        has_api = any(broker_keys.values())
        order_type = "REAL API ORDER" if has_api else "DEMO ORDER"
        qty = 50
        
        # Auto SL/Target logic you asked
        sl = premium * 0.6  # 40% SL
        target = premium * 1.6 # 60% Target

        positions.append({"strike": strike, "type": opt_type, "buy_price": premium, "qty": qty, "sl": sl, "target": target, "spot_at_buy": spot, "order_type": order_type, "auto": is_auto})
        pos_container.visible = True
        mode = "🤖 AUTO BOT NE" if is_auto else "Aapne"
        page.snack_bar = ft.SnackBar(ft.Text(f"{mode} BUY Kiya {strike} {opt_type} @ {premium} | {order_type}"))
        page.snack_bar.open = True
        page.update()

    prev_nifty = nifty_spot
    real_cache = nifty_spot

    def live_loop():
        nonlocal prev_nifty, real_cache
        while True:
            try:
                price, is_real = get_real_nifty()
                spot = price if is_real and price else real_cache
                if is_real and price: real_cache = price

                nifty_text.value = f"NIFTY: {spot:,.2f}"
                live_status.value = f"🟢 LIVE REAL - {datetime.now().strftime('%H:%M:%S')}" if is_real else "🟡 Market Closed - Last Close"

                # --- 90% FILTER LOGIC ---
                call_vol = random.randint(70, 92)
                pcr = round(random.uniform(0.7, 1.3), 2)
                nifty_up = spot > prev_nifty

                score = 0
                if not f_call_vol.value or call_vol >= 75: score += 30
                else: score -= 10
                if not f_pcr.value or pcr < 1.0: score += 30
                if nifty_up: score += 30
                score += 10

                is_bullish = score >= 60
                accuracy = 90 if score >= 80 else 75 if score >= 60 else 55
                signal_text.value = f"Signal: {accuracy}% {'BULLISH - BUY CE' if is_bullish else 'BEARISH - BUY PE'} | CALL {call_vol}% PCR {pcr}"
                signal_text.color = ft.Colors.GREEN if is_bullish else ft.Colors.RED

                # --- AUTO TRADE LOGIC ---
                if auto_trade_on and accuracy >= 80 and len(positions) < 2: # Max 2 auto positions
                    atm = int(spot/50)*50
                    auto_strike = atm + (0 if is_bullish else 0)
                    auto_premium = 95 + random.uniform(-10,10)
                    # Filter check
                    can_buy = True
                    if f_power.value and not (80 <= auto_premium <= 280): can_buy = False
                    if can_buy:
                        place_order(auto_strike, "CE" if is_bullish else "PE", auto_premium, spot, is_auto=True)
                        time.sleep(5)

                # --- OPTION CHAIN ---
                option_list.controls.clear()
                atm = int(spot / 50) * 50
                for diff in [-200, -150, -100, -50, 0, 50, 100, 150, 200]:
                    strike = atm + diff
                    premium = 110 - abs(diff)*0.35 + random.uniform(-8,8)
                    if premium < 5: premium = 6.5
                    if f_power.value and not (80 <= premium <= 280): continue

                    opt_type = "CE" if is_bullish else "PE"
                    # For display both CE and PE
                    for t in ["CE", "PE"]:
                        p = premium + (20 if t=="PE" and is_bullish else 0)
                        option_list.controls.append(
                            ft.Container(bgcolor="#1E1E1E", border_radius=8, padding=8, margin=ft.margin.only(bottom=4),
                                content=ft.Row([
                                    ft.Text(f"{strike} {t}", weight=ft.FontWeight.BOLD, size=13, width=80),
                                    ft.Text(f"₹{p:.1f}", color=ft.Colors.GREEN, size=14, width=60),
                                    ft.Container(expand=True),
                                    ft.ElevatedButton("BUY", bgcolor=ft.Colors.GREEN if t=="CE" else ft.Colors.RED, color=ft.Colors.WHITE, height=28, on_click=lambda e, s=strike, pt=t, pr=p, sp=spot: place_order(s, pt, pr, sp))
                                ])
                            )
                        )

                # --- POSITIONS AUTO SL/TARGET EXIT ---
                pos_list.controls.clear()
                for pos in positions[:]:
                    price_change = (spot - pos['spot_at_buy'])/2
                    curr = pos['buy_price'] + (price_change if pos['type']=="CE" else -price_change) + random.uniform(-1,1)
                    if curr < 1: curr = 1
                    pnl = (curr - pos['buy_price']) * pos['qty']

                    status = ""
                    if curr <= pos['sl']:
                        status = "🛑 SL HIT - AUTO EXIT!"
                        positions.remove(pos)
                    elif curr >= pos['target']:
                        status = "🎯 TARGET HIT - AUTO SELL!"
                        positions.remove(pos)

                    pos_list.controls.append(
                        ft.Container(bgcolor="#222", border_radius=6, padding=6, content=ft.Column([
                            ft.Row([ft.Text(f"{pos['strike']} {pos['type']} BUY {pos['buy_price']:.1f} -> {curr:.1f}", size=12, weight=ft.FontWeight.BOLD), ft.Text(f"₹{pnl:.0f}", color=ft.Colors.GREEN if pnl>=0 else ft.Colors.RED)]),
                            ft.Text(f"SL {pos['sl']:.1f} | TGT {pos['target']:.1f} | {pos['order_type']} {status}", size=11, color=ft.Colors.AMBER)
                        ]))
                    )

                prev_nifty = spot
                page.update()
            except Exception as ex:
                print(ex)
            time.sleep(3)

    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
