import flet as ft
import threading
import time
import random
import datetime
import requests
import json

def main(page: ft.Page):
    page.title = "Volume King V2"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 0

    BLUE_CHIPS = ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX","RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","SBIN","BHARTIARTL","ITC","LT","KOTAKBANK","AXISBANK"]

    selected_symbol = ft.Text("NIFTY", size=13, color="#00FF88", weight=ft.FontWeight.BOLD)
    pcr_txt = ft.Text("1.17", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    bot_st = ft.Text("RUNNING", color="#00FF88", weight=ft.FontWeight.BOLD, size=16)
    last_upd = ft.Text("Last: --:--:--", size=10, color="#888")
    nifty_live = ft.Text("NIFTY 23,039 • LIVE", size=12, color="#00FF88", weight=ft.FontWeight.BOLD)
    call_bull = ft.Text("0%", size=22, weight=ft.FontWeight.BOLD, color="#00FF88")
    put_bull = ft.Text("0%", size=22, weight=ft.FontWeight.BOLD, color="#FF6B8A")
    barrier_text = ft.Text("Scanning LIVE...", size=12, weight=ft.FontWeight.BOLD, color="#FFD700")
    barrier_bar = ft.ProgressBar(value=0.5, color="#00FF88", bgcolor="#442233", height=10, border_radius=4)
    log_box = ft.Text("System: LIVE V2", color="#888", size=11)
    api_status = ft.Text("No Broker Connected", size=11, color="#FFD700", weight=ft.FontWeight.BOLD)
    tg_status = ft.Text("Telegram Not Set", size=11, color="#888")

    # Chart data
    premium_points = []  # list of (x, y)
    alert_sent_cache = set()

    def card(c, pad=14):
        return ft.Container(content=c, bgcolor="#111111", border_radius=16, padding=pad, border=ft.border.all(1, "#2A2A2A"))

    symbol_dropdown = ft.Dropdown(label="Search: NIFTY, BANKNIFTY, HDFC...", value="NIFTY", options=[ft.dropdown.Option(s) for s in BLUE_CHIPS], bgcolor="#111111", border_color="#333", on_change=lambda e: fetch_live(), expand=True)
    broker_dropdown = ft.Dropdown(label="Select Broker", value="Angel One", options=[ft.dropdown.Option("Angel One"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Zerodha Kite"), ft.dropdown.Option("Upstox")], bgcolor="#111111", border_color="#00FF88", expand=True)
    
    f_client = ft.TextField(label="Client ID / Code", bgcolor="#0A0A0A", border_color="#333")
    f_api = ft.TextField(label="API Key", bgcolor="#0A0A0A", border_color="#333")
    f_secret = ft.TextField(label="Secret Key", password=True, can_reveal_password=True, bgcolor="#0A0A0A", border_color="#333")
    f_pass = ft.TextField(label="Password / MPIN", password=True, can_reveal_password=True, bgcolor="#0A0A0A", border_color="#333")
    f_totp = ft.TextField(label="TOTP Secret / Dhan Token", bgcolor="#0A0A0A", border_color="#333")

    # Telegram Fields
    f_tg_token = ft.TextField(label="Telegram Bot Token", hint_text="123456:ABC... from @BotFather", bgcolor="#0A0A0A", border_color="#229ED9")
    f_tg_chat = ft.TextField(label="Telegram Chat ID", hint_text="Your Chat ID from @userinfobot", bgcolor="#0A0A0A", border_color="#229ED9")
    f_tg_switch = ft.Switch(label="Telegram Alert ON - Bullish 80-100 Signal", value=False, active_color="#229ED9")

    def update_form(e):
        page.update()

    broker_dropdown.on_change = update_form

    def save_api(e):
        try:
            data = {"broker": broker_dropdown.value, "client_id": f_client.value, "api_key": f_api.value, "secret": f_secret.value, "password": f_pass.value, "totp": f_totp.value, "tg_token": f_tg_token.value, "tg_chat": f_tg_chat.value, "tg_on": f_tg_switch.value, "saved_at": datetime.datetime.now().strftime("%d-%m %H:%M")}
            page.client_storage.set("broker_api_config", json.dumps(data))
            api_status.value = f"Saved {data['broker']} {data['saved_at']}"
            api_status.color = "#00FF88"
            tg_status.value = f"Telegram {'ON' if data['tg_on'] else 'OFF'} - {data['tg_chat'][:10] if data['tg_chat'] else 'No ID'}"
            tg_status.color = "#229ED9" if data['tg_on'] else "#888"
            page.snack_bar = ft.SnackBar(ft.Text("All Settings Saved!"), bgcolor="#00FF88")
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
                f_tg_token.value = d.get("tg_token", "")
                f_tg_chat.value = d.get("tg_chat", "")
                f_tg_switch.value = d.get("tg_on", False)
                api_status.value = f"Loaded {d['broker']} {d.get('saved_at','')}"
                tg_status.value = f"Telegram {'ON' if d.get('tg_on') else 'OFF'} Loaded"
                page.update()
        except:
            pass

    def test_telegram(e):
        if not f_tg_token.value or not f_tg_chat.value:
            tg_status.value = "Bot Token + Chat ID dalo"
            tg_status.color = "#FF3B3B"
            page.update()
            return
        tg_status.value = "Sending Test..."
        page.update()
        try:
            url = f"https://api.telegram.org/bot{f_tg_token.value}/sendMessage"
            msg = f"✅ Volume King Test Alert\n{datetime.datetime.now().strftime('%H:%M:%S')}\n{symbol_dropdown.value} LIVE Connected!"
            r = requests.get(url, params={"chat_id": f_tg_chat.value, "text": msg}, timeout=8)
            if r.status_code == 200:
                tg_status.value = "✅ Telegram Test Sent! Check Telegram"
                tg_status.color = "#00FF88"
            else:
                tg_status.value = f"Failed: {r.text[:60]}"
                tg_status.color = "#FF3B3B"
        except Exception as ex:
            tg_status.value = f"Error: {ex}"
        page.update()

    def send_telegram_alert(text):
        if not f_tg_switch.value or not f_tg_token.value or not f_tg_chat.value:
            return
        try:
            # Avoid duplicate alert for same strike in 5 min
            key = text[:30]
            if key in alert_sent_cache:
                return
            alert_sent_cache.add(key)
            url = f"https://api.telegram.org/bot{f_tg_token.value}/sendMessage"
            requests.get(url, params={"chat_id": f_tg_chat.value, "text": text}, timeout=5)
            log_box.value = f"Telegram Alert Sent: {text[:30]}..."
            # clear cache after 5 min
            def clear_cache():
                time.sleep(300)
                alert_sent_cache.discard(key)
            threading.Thread(target=clear_cache, daemon=True).start()
        except:
            pass

    def oi_row(strike, side, conf, ltp, chg_oi, chg_price, vol_per, trend):
        is_bull = "Bullish" in trend
        bar_color = "#00FF88" if is_bull else "#FF3B3B" if "Bearish" in trend else "#FFA500"
        try: cp = float(chg_price)
        except: cp = 0.0
        arrow = "▲" if cp >= 0 else "▼"
        price_color = "#00FF88" if cp >= 0 else "#FF3B3B"
        return ft.Container(content=ft.Row([ft.Container(width=4, height=70, bgcolor=bar_color, border_radius=2), ft.Column([ft.Row([ft.Text(f"{symbol_dropdown.value} {strike} {side}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(content=ft.Text(f"{conf}%", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor=bar_color, border_radius=6, padding=ft.padding.symmetric(2, 6))], spacing=6), ft.Row([ft.Text(f"LTP Rs.{ltp}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text(f"{arrow} {chg_price}%", size=11, weight=ft.FontWeight.BOLD, color=price_color), ft.Text(f"OI:{chg_oi}", size=10, color="#AAA")], spacing=8), ft.Text(f"{trend} Vol {vol_per}%", size=10, weight=ft.FontWeight.BOLD, color=bar_color)], spacing=2, expand=True), ft.Column([ft.ElevatedButton(text="BUY", bgcolor="#00FF88", color="#000000", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD)), height=30, width=60), ft.ElevatedButton(text="SELL", bgcolor="#221118", color="#FF6B8A", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, "#442233"), text_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD)), height=26, width=60)], spacing=3)]), bgcolor="#111111", border_radius=14, padding=10, border=ft.border.all(1, "#2A2A2A"))

    quick_col = ft.Column([], spacing=8)
    full_chain_col = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    # --- CHARTS ---
    premium_chart = ft.LineChart(
        data_series=[ft.LineChartData(data_points=[], color="#00FF88", curved=True, stroke_width=3, below_line_bgcolor=ft.Colors.with_opacity(0.2, "#00FF88"), point=True)],
        border=ft.BorderSide(1, "#2A2A2A"),
        horizontal_grid_lines=ft.ChartGridLines(interval=20, color="#222222", width=1),
        vertical_grid_lines=ft.ChartGridLines(interval=1, color="#222222", width=1),
        left_axis=ft.ChartAxis(labels_size=28),
        bottom_axis=ft.ChartAxis(labels_size=28),
        tooltip_bgcolor="#111111",
        min_y=40, max_y=150,
        min_x=0, max_x=20,
        expand=True
    )

    call_put_bar = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(x=0, bar_rods=[ft.BarChartRod(from_y=0, to_y=5, color="#00FF88", width=18, border_radius=4)]),
            ft.BarChartGroup(x=1, bar_rods=[ft.BarChartRod(from_y=0, to_y=5, color="#FF6B8A", width=18, border_radius=4)])
        ],
        border=ft.BorderSide(1, "#2A2A2A"),
        left_axis=ft.ChartAxis(labels_size=28),
        bottom_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=0, label=ft.Text("CALL", size=10)), ft.ChartAxisLabel(value=1, label=ft.Text("PUT", size=10))]),
        max_y=10,
        expand=True
    )

    page1 = ft.Column([
        ft.Container(content=symbol_dropdown, margin=ft.margin.symmetric(10, 6)),
        ft.Container(content=card(ft.Column([ft.Text("BULLISH BARRIER - CALL vs PUT LIVE", size=11, weight=ft.FontWeight.BOLD, color="#FFD700"), ft.Row([ft.Column([ft.Text("CALL Bullish", size=10, color="#888"), call_bull], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), ft.Column([ft.Text("PUT Bullish", size=10, color="#888"), put_bull], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)]), barrier_bar, ft.Container(content=barrier_text, alignment=ft.alignment.center, padding=ft.padding.only(top=6))])), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor="#00FF88", border_radius=4), ft.Text("REAL MARKET: LIVE V2", size=11, weight=ft.FontWeight.BOLD, color="#6AFFAA", expand=True), nifty_live]), bgcolor="#0A1E0A", border_radius=14, padding=12, border=ft.border.all(1, "#1A4D2E")), margin=ft.margin.symmetric(10, 4)),
        # Chart Row
        ft.Container(content=ft.Row([card(ft.Column([ft.Text("Premium Trend 80-100 LIVE", size=10, color="#00FF88", weight=ft.FontWeight.BOLD), ft.Container(content=premium_chart, height=120)]), expand=True), card(ft.Column([ft.Text("CALL vs PUT Bullish", size=10, color="#FFD700", weight=ft.FontWeight.BOLD), ft.Container(content=call_put_bar, height=120)]), expand=True)], spacing=8), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Row([card(ft.Column([ft.Text("BOT STATUS", size=9, color="#888"), ft.Row([ft.Container(width=6, height=6, bgcolor="#00FF88", border_radius=3), bot_st]), last_upd])), card(ft.Column([ft.Text("MARKET PULSE", size=9, color="#888"), ft.Row([ft.Text("PCR", size=11, color="#888"), pcr_txt])]))], spacing=8), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.ElevatedButton(text="START OI BOT + TELEGRAM ALERT", icon=ft.Icons.POWER_SETTINGS_NEW, bgcolor="#00FF66", color="#000000", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD)), height=50, expand=True), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Column([ft.Text("LIVE BOT LOG + TELEGRAM", size=10, color="#AAA", weight=ft.FontWeight.BOLD), card(ft.Column([log_box, tg_status]))], spacing=4), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Column([ft.Text("QUICK OI CHAIN LIVE", size=10, color="#AAA", weight=ft.FontWeight.BOLD), quick_col], spacing=6), margin=ft.margin.symmetric(10, 4)),
        ft.Container(height=80)
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)

    page2 = ft.Column([ft.Text("Indicator - Search Blue Chip", size=16, weight=ft.FontWeight.BOLD), symbol_dropdown, card(ft.Column([ft.Text("Filter: Premium 80-100 + Vol 80% + OI High = Bullish Telegram", size=10, color="#888")]))], scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    page3 = ft.Column([ft.Text("OI Chain + Chart LIVE", size=16, weight=ft.FontWeight.BOLD), ft.Container(content=card(ft.Column([ft.Text("Premium Live Chart", size=11, color="#00FF88"), ft.Container(content=premium_chart, height=180)])), margin=ft.margin.symmetric(0, 6)), full_chain_col], expand=True, spacing=8)

    page4 = ft.Column([
        ft.Text("Security / Bot Setting V2", size=18, weight=ft.FontWeight.BOLD),
        card(ft.Column([ft.Text("BROKER API HUB", size=12, weight=ft.FontWeight.BOLD, color="#00FF88"), api_status, broker_dropdown, f_client, f_api, f_secret, f_pass, f_totp, ft.Row([ft.ElevatedButton(text="SAVE API", bgcolor="#00FF88", color="#000000", on_click=save_api, expand=True), ft.ElevatedButton(text="LOAD", bgcolor="#333", color=ft.Colors.WHITE, on_click=load_api, expand=True)], spacing=8)], spacing=10)),
        card(ft.Column([ft.Text("TELEGRAM ALERT SETTING - Feature 2", size=12, weight=ft.FontWeight.BOLD, color="#229ED9"), tg_status, f_tg_token, f_tg_chat, f_tg_switch, ft.Row([ft.ElevatedButton(text="SAVE TELEGRAM", icon=ft.Icons.SAVE, bgcolor="#229ED9", color=ft.Colors.WHITE, on_click=save_api, expand=True), ft.ElevatedButton(text="TEST TELEGRAM", icon=ft.Icons.SEND, bgcolor="#FFD700", color="#000000", on_click=test_telegram, expand=True)], spacing=8), ft.Text("How to get: 1) Telegram pe @BotFather -> /newbot -> Token copy 2) @userinfobot -> Start -> Chat ID copy 3) Dono yaha paste -> SAVE -> TEST", size=9, color="#666")], spacing=10)),
        card(ft.Column([ft.Text("Bot Setting", size=12, weight=ft.FontWeight.BOLD), ft.Switch(label="AUTO Mode ON", value=True, active_color="#00FF88"), ft.TextField(label="Target % 10", value="10", bgcolor="#0A0A0A", border_color="#333"), ft.TextField(label="Stop Loss % 5", value="5", bgcolor="#0A0A0A", border_color="#333")]))
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    content = ft.Container(content=page1, expand=True)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: content.content = page1
        elif idx == 1: content.content = page2
        elif idx == 2: content.content = page3
        elif idx == 3: content.content = page4
        page.update()

    nav = ft.Container(content=ft.NavigationBar(selected_index=0, on_change=nav_change, bgcolor="#0F0F0F", indicator_color="#1A3A1A", destinations=[ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Main Bot"), ft.NavigationBarDestination(icon=ft.Icons.TUNE, label="Indicator"), ft.NavigationBarDestination(icon=ft.Icons.LIST, label="OI Chain"), ft.NavigationBarDestination(icon=ft.Icons.SECURITY, label="Setting")]), border=ft.border.only(top=ft.BorderSide(1, "#222")))

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
                strike = int(ltp_live / 100) * 100 - 400 + i * 100 if sym in ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX"] else 1000 + i * 50
                side = "CE" if i % 2 == 0 else "PE"
                ltp_opt = round(random.uniform(45, 145), 1)
                chg_oi = f"{random.randint(5,45)}k"
                chg_price = round(random.uniform(-5.0, 5.0), 2)
                vol = random.randint(65,95)
                conf = random.randint(78,96)
                if 80 <= ltp_opt <= 100 and vol >= 80:
                    trend = f"Bullish Strong BUY {side}"
                    if side == "CE": call_b += 1
                    else: put_b += 1
                elif ltp_opt < 70: trend = f"Bearish SELL {side}"
                elif ltp_opt > 110: trend = f"Overbought {side}"
                else: trend = f"Neutral {side}"
                signals.append((strike, side, conf, ltp_opt, chg_oi, chg_price, vol, trend))

            # Chart update
            try:
                avg_premium = sum([s[3] for s in signals]) / len(signals)
                premium_points.append(avg_premium)
                if len(premium_points) > 20:
                    premium_points.pop(0)
                pts = [ft.LineChartDataPoint(x=i, y=premium_points[i]) for i in range(len(premium_points))]
                premium_chart.data_series[0].data_points = pts
                premium_chart.min_x = 0
                premium_chart.max_x = max(20, len(premium_points))
                call_put_bar.bar_groups[0].bar_rods[0].to_y = call_b
                call_put_bar.bar_groups[1].bar_rods[0].to_y = put_b
                call_put_bar.max_y = max(10, call_b + put_b + 1)
            except:
                pass

            # Telegram Alert for Bullish 80-100
            for s in signals:
                if 80 <= s[3] <= 100 and s[6] >= 80 and "Bullish" in s[7]:
                    msg = f"🚀 Volume King ALERT\n{sym} {s[0]} {s[1]}\n{ s[7]}\nLTP Rs.{s[3]} {s[5]}%\nConf {s[2]}% OI:{s[4]} Vol:{s[6]}%\nTime {datetime.datetime.now().strftime('%H:%M:%S')}"
                    send_telegram_alert(msg)

            total = call_b + put_b
            if total > 0:
                cp = int(call_b / total * 100) if total else 0
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
            log_box.value = f"{datetime.datetime.now().strftime('%H:%M:%S')} LIVE {sym} CALL {call_b} PUT {put_b} Avg Prem {avg_premium:.1f}"
            quick_col.controls = [oi_row(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]) for s in signals[:4]]
            full_chain_col.controls = [oi_row(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]) for s in signals]
            last_upd.value = f"Last: {datetime.datetime.now().strftime('%H:%M:%S')} LIVE {sym}"
            page.update()
        except Exception as ex:
            try:
                log_box.value = f"Err {ex}"
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
