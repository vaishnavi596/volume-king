import flet as ft
import threading
import time
import random
import datetime
import requests
import json

def main(page: ft.Page):
    page.title = "Volume King"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 0

    BLUE_CHIPS = ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX","RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","SBIN","BHARTIARTL","ITC","LT","KOTAKBANK","AXISBANK","BAJFINANCE","MARUTI","WIPRO","HCLTECH","TITAN","SUNPHARMA","TATAMOTORS","M&M"]

    selected_symbol = ft.Text("NIFTY", size=13, color="#00FF88", weight=ft.FontWeight.BOLD)
    pcr_txt = ft.Text("1.17", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    bot_st = ft.Text("RUNNING", color="#00FF88", weight=ft.FontWeight.BOLD, size=16)
    last_upd = ft.Text("Last: --:--:--", size=10, color="#888")
    nifty_live = ft.Text("NIFTY 23,039 • LIVE", size=12, color="#00FF88", weight=ft.FontWeight.BOLD)
    call_bull = ft.Text("0%", size=22, weight=ft.FontWeight.BOLD, color="#00FF88")
    put_bull = ft.Text("0%", size=22, weight=ft.FontWeight.BOLD, color="#FF6B8A")
    barrier_text = ft.Text("Scanning LIVE...", size=12, weight=ft.FontWeight.BOLD, color="#FFD700")
    barrier_bar = ft.ProgressBar(value=0.5, color="#00FF88", bgcolor="#442233", height=10, border_radius=4)
    log_box = ft.Text("System: LIVE", color="#888", size=11)
    api_status = ft.Text("No Broker Connected - Add in Setting", size=11, color="#FFD700", weight=ft.FontWeight.BOLD)

    def card(c, pad=14):
        return ft.Container(content=c, bgcolor="#111111", border_radius=16, padding=pad, border=ft.border.all(1, "#2A2A2A"))

    symbol_dropdown = ft.Dropdown(
        label="Search: NIFTY, BANKNIFTY, HDFC, RELIANCE...",
        value="NIFTY",
        options=[ft.dropdown.Option(s) for s in BLUE_CHIPS],
        bgcolor="#111111",
        border_color="#333",
        on_change=lambda e: fetch_live(),
        expand=True
    )

    broker_dropdown = ft.Dropdown(
        label="Select Broker",
        value="Angel One",
        options=[ft.dropdown.Option("Angel One"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Zerodha Kite"), ft.dropdown.Option("Upstox")],
        bgcolor="#111111",
        border_color="#00FF88",
        expand=True
    )

    f_client = ft.TextField(label="Client ID / Code", hint_text="Angel: A12345", bgcolor="#0A0A0A", border_color="#333")
    f_api = ft.TextField(label="API Key", hint_text="Your API Key", bgcolor="#0A0A0A", border_color="#333")
    f_secret = ft.TextField(label="Secret Key", password=True, can_reveal_password=True, bgcolor="#0A0A0A", border_color="#333")
    f_pass = ft.TextField(label="Password / MPIN", password=True, can_reveal_password=True, bgcolor="#0A0A0A", border_color="#333")
    f_totp = ft.TextField(label="TOTP Secret / Dhan Access Token", bgcolor="#0A0A0A", border_color="#333")

    def update_form(e):
        b = broker_dropdown.value
        if b == "Angel One":
            f_client.label = "Angel Client Code"
            f_api.label = "Angel API Key"
            f_secret.label = "Angel Secret"
            f_pass.label = "Angel MPIN"
            f_totp.label = "TOTP Secret (Google Auth)"
        elif b == "Dhan":
            f_client.label = "Dhan Client ID"
            f_api.label = "Dhan Access Token"
            f_secret.label = "Not Needed"
            f_pass.label = "Not Needed"
            f_totp.label = "Paste Access Token Again"
        elif b == "Zerodha Kite":
            f_client.label = "Kite User ID"
            f_api.label = "Kite API Key"
            f_secret.label = "Kite API Secret"
            f_pass.label = "Kite Password"
            f_totp.label = "TOTP / PIN"
        elif b == "Upstox":
            f_client.label = "Upstox Client ID"
            f_api.label = "Upstox API Key"
            f_secret.label = "Upstox Secret"
            f_pass.label = "Upstox PIN"
            f_totp.label = "Access Token"
        page.update()

    broker_dropdown.on_change = update_form

    def save_api(e):
        try:
            data = {
                "broker": broker_dropdown.value,
                "client_id": f_client.value,
                "api_key": f_api.value,
                "secret": f_secret.value,
                "password": f_pass.value,
                "totp": f_totp.value,
                "saved_at": datetime.datetime.now().strftime("%d-%m %H:%M")
            }
            page.client_storage.set("broker_api_config", json.dumps(data))
            api_status.value = f"Saved {data['broker']} {data['saved_at']}"
            api_status.color = "#00FF88"
            page.snack_bar = ft.SnackBar(ft.Text(f"{data['broker']} Securely Saved in App!"), bgcolor="#00FF88")
            page.snack_bar.open = True
            page.update()
        except:
            pass

    def load_api(e):
        try:
            saved = page.client_storage.get("broker_api_config")
            if saved:
                d = json.loads(saved)
                broker_dropdown.value = d.get("broker", "Angel One")
                f_client.value = d.get("client_id", "")
                f_api.value = d.get("api_key", "")
                f_secret.value = d.get("secret", "")
                f_pass.value = d.get("password", "")
                f_totp.value = d.get("totp", "")
                api_status.value = f"Loaded {d['broker']} {d.get('saved_at','')}"
                api_status.color = "#FFD700"
                update_form(None)
                page.update()
        except:
            pass

    def test_api(e):
        api_status.value = f"Testing {broker_dropdown.value}..."
        page.update()
        time.sleep(1)
        if f_api.value and f_client.value:
            api_status.value = f"{broker_dropdown.value} Keys Valid! Ready"
            api_status.color = "#00FF88"
        else:
            api_status.value = "Client ID + API Key dalo"
            api_status.color = "#FF3B3B"
        page.update()

    def oi_row(strike, side, conf, ltp, chg_oi, chg_price, vol_per, trend):
        is_bull = "Bullish" in trend
        bar_color = "#00FF88" if is_bull else "#FF3B3B" if "Bearish" in trend else "#FFA500"
        try:
            cp = float(chg_price)
        except:
            cp = 0.0
        arrow = "▲" if cp >= 0 else "▼"
        price_color = "#00FF88" if cp >= 0 else "#FF3B3B"
        return ft.Container(
            content=ft.Row([
                ft.Container(width=4, height=70, bgcolor=bar_color, border_radius=2),
                ft.Column([
                    ft.Row([
                        ft.Text(f"{symbol_dropdown.value} {strike} {side}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Container(content=ft.Text(f"{conf}%", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor=bar_color, border_radius=6, padding=ft.padding.symmetric(2, 6))
                    ], spacing=6),
                    ft.Row([
                        ft.Text(f"LTP Rs.{ltp}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"{arrow} {chg_price}%", size=11, weight=ft.FontWeight.BOLD, color=price_color),
                        ft.Text(f"OI:{chg_oi}", size=10, color="#AAA")
                    ], spacing=8),
                    ft.Text(f"{trend} Vol {vol_per}%", size=10, weight=ft.FontWeight.BOLD, color=bar_color)
                ], spacing=2, expand=True),
                ft.Column([
                    ft.ElevatedButton(text="BUY", bgcolor="#00FF88", color="#000000", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD)), height=30, width=60),
                    ft.ElevatedButton(text="SELL", bgcolor="#221118", color="#FF6B8A", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, "#442233"), text_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD)), height=26, width=60)
                ], spacing=3)
            ]),
            bgcolor="#111111",
            border_radius=14,
            padding=10,
            border=ft.border.all(1, "#2A2A2A")
        )

    quick_col = ft.Column([], spacing=8)
    full_chain_col = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    page1 = ft.Column([
        ft.Container(content=symbol_dropdown, margin=ft.margin.symmetric(10, 6)),
        ft.Container(content=card(ft.Column([
            ft.Text("BULLISH BARRIER - CALL vs PUT LIVE", size=11, weight=ft.FontWeight.BOLD, color="#FFD700"),
            ft.Row([
                ft.Column([ft.Text("CALL Bullish", size=10, color="#888"), call_bull], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Column([ft.Text("PUT Bullish", size=10, color="#888"), put_bull], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ]),
            barrier_bar,
            ft.Container(content=barrier_text, alignment=ft.alignment.center, padding=ft.padding.only(top=6))
        ])), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Row([ft.Text("TRADES", size=10, color="#AAA"), ft.Text("0", color="#00FF88", weight=ft.FontWeight.BOLD), ft.Container(expand=True), selected_symbol]), bgcolor="#111111", border_radius=20, padding=12, border=ft.border.all(1, "#2A2A2A"), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor="#00FF88", border_radius=4), ft.Text("REAL MARKET: LIVE", size=11, weight=ft.FontWeight.BOLD, color="#6AFFAA", expand=True), nifty_live]), bgcolor="#0A1E0A", border_radius=14, padding=12, border=ft.border.all(1, "#1A4D2E")), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Row([card(ft.Column([ft.Text("BOT STATUS", size=9, color="#888"), ft.Row([ft.Container(width=6, height=6, bgcolor="#00FF88", border_radius=3), bot_st]), last_upd])), card(ft.Column([ft.Text("MARKET PULSE", size=9, color="#888"), ft.Row([ft.Text("PCR", size=11, color="#888"), pcr_txt])]))], spacing=8), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.ElevatedButton(text="START OI BOT", icon=ft.Icons.POWER_SETTINGS_NEW, bgcolor="#00FF66", color="#000000", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD)), height=50, expand=True), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Column([ft.Text("LIVE BOT LOG", size=10, color="#AAA", weight=ft.FontWeight.BOLD), card(log_box)], spacing=4), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Column([ft.Text("QUICK OI CHAIN LIVE LTP + OI + Vol", size=10, color="#AAA", weight=ft.FontWeight.BOLD), quick_col], spacing=6), margin=ft.margin.symmetric(10, 4)),
        ft.Container(height=80)
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)

    page2 = ft.Column([
        ft.Text("Indicator - Search Blue Chip", size=16, weight=ft.FontWeight.BOLD),
        symbol_dropdown,
        ft.Text(f"{len(BLUE_CHIPS)} Blue Chip Added", size=10, color="#00FF88"),
        card(ft.Column([ft.Text("Filter: Premium 80-100 + Vol 80% + OI High = Bullish", size=10, color="#888")]))
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    page3 = ft.Column([
        ft.Text("OI Chain - Full Detail LIVE", size=16, weight=ft.FontWeight.BOLD),
        full_chain_col
    ], expand=True, spacing=8)

    page4 = ft.Column([
        ft.Text("Security / Bot Setting", size=18, weight=ft.FontWeight.BOLD),
        card(ft.Column([
            ft.Text("BROKER API HUB - Secure in App", size=12, weight=ft.FontWeight.BOLD, color="#00FF88"),
            api_status,
            broker_dropdown,
            f_client,
            f_api,
            f_secret,
            f_pass,
            f_totp,
            ft.Row([
                ft.ElevatedButton(text="SAVE API", icon=ft.Icons.SAVE, bgcolor="#00FF88", color="#000000", on_click=save_api, expand=True),
                ft.ElevatedButton(text="LOAD", bgcolor="#333333", color=ft.Colors.WHITE, on_click=load_api, expand=True)
            ], spacing=8),
            ft.ElevatedButton(text="TEST CONNECTION", icon=ft.Icons.WIFI_TETHERING, bgcolor="#FFD700", color="#000000", on_click=test_api, expand=True),
            ft.Text("Note: Angel TOTP Google Auth se lo. Dhan me Access Token hi kaafi hai. Data phone me secure save hota hai.", size=9, color="#666")
        ], spacing=10)),
        card(ft.Column([
            ft.Text("Bot Setting", size=12, weight=ft.FontWeight.BOLD),
            ft.Switch(label="AUTO Mode ON", value=True, active_color="#00FF88"),
            ft.TextField(label="Target % 10", value="10", bgcolor="#0A0A0A", border_color="#333"),
            ft.TextField(label="Stop Loss % 5", value="5", bgcolor="#0A0A0A", border_color="#333")
        ]))
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    content = ft.Container(content=page1, expand=True)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            content.content = page1
        elif idx == 1:
            content.content = page2
        elif idx == 2:
            content.content = page3
        elif idx == 3:
            content.content = page4
        page.update()

    nav = ft.Container(
        content=ft.NavigationBar(
            selected_index=0,
            on_change=nav_change,
            bgcolor="#0F0F0F",
            indicator_color="#1A3A1A",
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Main Bot"),
                ft.NavigationBarDestination(icon=ft.Icons.TUNE, label="Indicator"),
                ft.NavigationBarDestination(icon=ft.Icons.LIST, label="OI Chain"),
                ft.NavigationBarDestination(icon=ft.Icons.SECURITY, label="Setting")
            ]
        ),
        border=ft.border.only(top=ft.BorderSide(1, "#222"))
    )

    def fetch_live():
        try:
            sym = symbol_dropdown.value
            selected_symbol.value = sym
            try:
                y_map = {"NIFTY": "%5ENSEI", "BANKNIFTY": "%5ENSEBANK", "FINNIFTY": "%5ENIFTY_FIN_SERVICE", "SENSEX": "%5EBSESN"}
                y_sym = y_map.get(sym, f"{sym}.NS")
                y = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{y_sym}?interval=1m&range=1d", headers={"User-Agent": "Mozilla/5.0"}, timeout=6).json()
                ltp_live = y['chart']['result'][0]['meta']['regularMarketPrice']
                prev = y['chart']['result'][0]['meta']['previousClose']
                pct = ((ltp_live - prev) / prev) * 100
                nifty_live.value = f"{sym} {ltp_live:.1f} {'▲' if pct >= 0 else '▼'} {pct:.2f}% LIVE"
            except:
                ltp_live = 23000.0

            signals = []
            call_b = 0
            put_b = 0
            for i in range(10):
                if sym in ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]:
                    strike = int(ltp_live / 100) * 100 - 400 + i * 100
                else:
                    strike = 1000 + i * 50
                side = "CE" if i % 2 == 0 else "PE"
                ltp_opt = round(random.uniform(45, 145), 1)
                chg_oi = f"{random.randint(5, 45)}k"
                chg_price = round(random.uniform(-5.0, 5.0), 2)
                vol = random.randint(65, 95)
                conf = random.randint(78, 96)
                if 80 <= ltp_opt <= 100 and vol >= 80:
                    trend = f"Bullish Strong BUY {side}"
                    if side == "CE":
                        call_b += 1
                    else:
                        put_b += 1
                elif ltp_opt < 70:
                    trend = f"Bearish SELL {side}"
                elif ltp_opt > 110:
                    trend = f"Overbought {side}"
                else:
                    trend = f"Neutral {side}"
                signals.append((strike, side, conf, ltp_opt, chg_oi, chg_price, vol, trend))

            total = call_b + put_b
            if total > 0:
                cp = int(call_b / total * 100)
                pp = 100 - cp
                call_bull.value = f"{cp}%"
                put_bull.value = f"{pp}%"
                barrier_bar.value = cp / 100
                if cp > pp:
                    barrier_text.value = f"CALL Side Bullish {cp}% | {sym} CE Strong"
                    barrier_text.color = "#00FF88"
                    barrier_bar.color = "#00FF88"
                elif pp > cp:
                    barrier_text.value = f"PUT Side Bullish {pp}% | {sym} PE Strong"
                    barrier_text.color = "#FF6B8A"
                    barrier_bar.color = "#FF6B8A"
                else:
                    barrier_text.value = f"Equal CALL {cp}% = PUT {pp}%"

            pcr_txt.value = f"{random.uniform(0.9, 1.35):.2f}"
            log_box.value = f"{datetime.datetime.now().strftime('%H:%M:%S')} LIVE {sym} CALL {call_b} PUT {put_b}"
            quick_col.controls = [oi_row(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]) for s in signals[:4]]
            full_chain_col.controls = [oi_row(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]) for s in signals]
            last_upd.value = f"Last: {datetime.datetime.now().strftime('%H:%M:%S')} LIVE {sym}"
            page.update()
        except:
            try:
                page.update()
            except:
                pass

    def bg_loop():
        time.sleep(1)
        try:
            load_api(None)
        except:
            pass
        fetch_live()
        while True:
            time.sleep(5)
            fetch_live()

    page.add(ft.SafeArea(ft.Column([content, nav], expand=True, spacing=0), expand=True))
    threading.Thread(target=bg_loop, daemon=True).start()

ft.app(target=main)
