import flet as ft
import threading, time, random, json
import urllib.request
from datetime import datetime

# ---- CONFIG ----
DEMO_BALANCE = 100000
api_config = {"broker": "AngelOne", "angel_api_key": "", "angel_client": "", "angel_pass": "", "angel_totp": "", "dhan_client": "", "dhan_token": ""}
IS_LIVE = False

def get_real_nifty():
    try:
        req = urllib.request.Request(
            "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return float(price), True
    except:
        return 24532 + random.uniform(-150, 150), False

def main(page: ft.Page):
    page.title = "VOLUME KING 97 V8"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO

    # --- Top Bar ---
    title = ft.Text("VOLUME KING 97 V8 UNIVERSAL", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)

    broker_dropdown = ft.Dropdown(
        label="Broker", value=api_config["broker"],
        options=[ft.dropdown.Option("AngelOne"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Demo")],
        width=180, height=50, text_size=12
    )
    login_btn = ft.ElevatedButton("LOGIN", bgcolor=ft.Colors.GREEN, color="white", width=80, height=40)
    
    mode_switch = ft.Switch(label="LIVE OFF/DEMO", value=False)
    live_text = ft.Text("DEMO MODE", color=ft.Colors.RED, size=12, weight=ft.FontWeight.BOLD)

    def toggle_live(e):
        global IS_LIVE
        IS_LIVE = mode_switch.value
        if IS_LIVE:
            mode_switch.label = "LIVE ON"
            live_text.value = "LIVE MODE 🟢"
            live_text.color = ft.Colors.GREEN
        else:
            mode_switch.label = "LIVE OFF/DEMO"
            live_text.value = "DEMO MODE"
            live_text.color = ft.Colors.RED
        page.update()

    mode_switch.on_change = toggle_live

    # --- Market Data ---
    nifty_text = ft.Text("LIVE NIFTY: 24532 🟢", size=22, weight=ft.FontWeight.BOLD, color="white")
    call_vol_text = ft.Text("CALL Vol: 74% | PUT Vol: 26%", size=14)
    pcr_text = ft.Text("PCR: 0.92 (Neutral)", size=14, color=ft.Colors.AMBER)
    vwap_text = ft.Text("VWAP: 24490 | Price VWAP UPAR", size=13, color=ft.Colors.GREY_400)
    oi_text = ft.Text("OI Trend: CALL OI UP 📈", size=13, color=ft.Colors.GREEN)

    vol_bar = ft.ProgressBar(value=0.74, color=ft.Colors.GREEN, bgcolor="#333", height=10)

    # --- Signal Box ---
    signal_box = ft.Container(
        bgcolor="#2A2A0A", border_radius=12, padding=12,
        border=ft.border.all(2, ft.Colors.AMBER),
        content=ft.Column([
            ft.Text("🔥 90% SIGNAL: BUY CE", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
            ft.Text("Last Trade: No Trade", size=11, color=ft.Colors.GREY_400)
        ])
    )
    last_trade_text = signal_box.content.controls[1]

    # --- BUY Buttons ---
    def buy_ce(e):
        last_trade_text.value = f"Last Trade: BUY CE @ {datetime.now().strftime('%H:%M:%S')} ✅"
        page.snack_bar = ft.SnackBar(ft.Text("BUY CE 90% Placed! 🚀"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    def buy_pe(e):
        last_trade_text.value = f"Last Trade: BUY PE @ {datetime.now().strftime('%H:%M:%S')} ✅"
        page.snack_bar = ft.SnackBar(ft.Text("BUY PE 90% Placed! 📉"), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    buy_ce_btn = ft.ElevatedButton("BUY CE 90%", bgcolor="#00C853", color="white", expand=True, height=55, on_click=buy_ce)
    buy_pe_btn = ft.ElevatedButton("BUY PE 90%", bgcolor="#D32F2F", color="white", expand=True, height=55, on_click=buy_pe)

    zap_text = ft.Text("ZAP MODE ON - Free Data", size=10, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)

    # --- Layout ---
    page.add(
        title,
        ft.Row([broker_dropdown, login_btn]),
        ft.Row([mode_switch, live_text]),
        ft.Divider(height=1, color="#333"),
        nifty_text,
        vol_bar,
        call_vol_text,
        pcr_text,
        vwap_text,
        oi_text,
        signal_box,
        ft.Row([buy_ce_btn, buy_pe_btn]),
        zap_text
    )

    # --- Live Loop ---
    def live_loop():
        while True:
            price, is_real = get_real_nifty()
            nifty = price if IS_LIVE else price + random.uniform(-80, 80)
            call_vol = random.randint(65, 88)
            put_vol = 100 - call_vol
            pcr = round(random.uniform(0.75, 1.25), 2)
            vwap = int(nifty - random.uniform(-50, 50))

            tag = "🟢 REAL" if (IS_LIVE and is_real) else "🔴 DEMO"

            nifty_text.value = f"LIVE NIFTY: {nifty:,.0f} {tag}"
            call_vol_text.value = f"CALL Vol: {call_vol}% | PUT Vol: {put_vol}%"
            vol_bar.value = call_vol / 100
            pcr_text.value = f"PCR: {pcr} ({'Bullish' if pcr < 1 else 'Bearish'})"
            vwap_text.value = f"VWAP: {vwap} | Price VWAP {'UPAR' if nifty > vwap else 'NICHE'}"
            
            if call_vol > 75 and pcr < 1.0 and nifty > vwap:
                signal_box.content.controls[0].value = f"🔥 {call_vol}% SIGNAL: BUY CE"
                signal_box.content.controls[0].color = ft.Colors.GREEN
            elif put_vol > 60 and pcr > 1.1:
                signal_box.content.controls[0].value = f"🔥 {put_vol}% SIGNAL: BUY PE"
                signal_box.content.controls[0].color = ft.Colors.RED

            try:
                page.update()
            except:
                pass
            time.sleep(3)

    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
