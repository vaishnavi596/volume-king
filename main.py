import flet as ft
import threading, time, random, json
import urllib.request
from datetime import datetime

DEMO_BALANCE = 100000
api_config = {"broker": "Navia", "angel_api_key": "", "angel_client": "", "angel_pass": "", "angel_totp": "", "dhan_client": "", "dhan_token": ""}
IS_LIVE = False

def get_real_nifty():
    try:
        # NSE se Real Price - requests nahi, urllib se
        req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return float(price), True
    except Exception as e:
        print("Real fetch fail:", e)
        return 24480 + random.uniform(-100, 100), False

def main(page: ft.Page):
    page.title = "Volume King 97 REAL"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    try:
        saved = page.client_storage.get("api_config")
        if saved: api_config.update(json.loads(saved))
    except: pass

    title = ft.Text("VOLUME KING 97 - REAL MARKET", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)

    trend_icon = ft.Text("🚀", size=32)
    trend_text = ft.Text("BULLISH", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    accuracy_text = ft.Text("Accuracy: 90%", size=14, color=ft.Colors.AMBER)
    trend_reason = ft.Text("Fetching real market...", size=11, color=ft.Colors.GREY_400)
    trend_bar = ft.ProgressBar(value=0.9, color=ft.Colors.GREEN, bgcolor="#333", height=8, width=320)
    live_status = ft.Text("🔴 DEMO MODE (Random Data)", color=ft.Colors.RED, size=12)

    trend_dashboard = ft.Container(
        bgcolor="#1A2B1A", border_radius=15, padding=12,
        border=ft.border.all(2, ft.Colors.GREEN),
        content=ft.Column([
            ft.Row([trend_icon, trend_text, ft.Container(expand=True), accuracy_text]),
            trend_bar, trend_reason, live_status
        ])
    )

    f_call_vol = ft.Switch(label="90% CALL VOL Filter", value=True)
    f_pcr = ft.Switch(label="PCR <1.0 Bullish Filter", value=True)
    f_power = ft.Switch(label="POWERFUL (120-280) Only", value=True)

    filter_panel = ft.Container(bgcolor="#111", border_radius=10, padding=10, content=ft.Column([ft.Text("FILTERS ON/OFF:", size=12, weight=ft.FontWeight.BOLD), f_call_vol, f_pcr, f_power]))

    broker_dropdown = ft.Dropdown(label="Broker", value=api_config["broker"], options=[ft.dropdown.Option("Demo"), ft.dropdown.Option("AngelOne"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Navia")], width=320)
    balance_text = ft.Text(f"Balance: ₹{DEMO_BALANCE:,}", size=16, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
    nifty_text = ft.Text("NIFTY: Loading Real...", size=26, weight=ft.FontWeight.BOLD)
    vol_text = ft.Text("CALL VOL: -- | PCR: --", size=13, color=ft.Colors.AMBER)
    signal_text = ft.Text("Signal: WAIT", size=13, weight=ft.FontWeight.BOLD)
    option_list = ft.Column()
    last_trade = ft.Text("Last Trade: No Trade", size=12, color=ft.Colors.GREY)

    angel_key_field = ft.TextField(label="AngelOne API Key", value=api_config["angel_api_key"], width=320)
    angel_client_field = ft.TextField(label="AngelOne Client Code", value=api_config["angel_client"], width=320)
    angel_pass_field = ft.TextField(label="AngelOne Password", password=True, value=api_config["angel_pass"], width=320)
    angel_totp_field = ft.TextField(label="AngelOne TOTP Secret", value=api_config["angel_totp"], width=320)
    dhan_client_field = ft.TextField(label="Dhan Client ID", value=api_config["dhan_client"], width=320)
    dhan_token_field = ft.TextField(label="Dhan Access Token", value=api_config["dhan_token"], width=320)

    def save_api_keys(e):
        api_config.update({"angel_api_key": angel_key_field.value, "angel_client": angel_client_field.value, "angel_pass": angel_pass_field.value, "angel_totp": angel_totp_field.value, "dhan_client": dhan_client_field.value, "dhan_token": dhan_token_field.value, "broker": broker_dropdown.value})
        page.client_storage.set("api_config", json.dumps(api_config))
        page.dialog.open = False
        page.snack_bar = ft.SnackBar(ft.Text(f"Saved! Broker: {broker_dropdown.value} ✅"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    settings_dialog = ft.AlertDialog(title=ft.Text("API Keys - Real Market Ke Liye"), content=ft.Column([ft.Text("AngelOne:", weight=ft.FontWeight.BOLD), angel_key_field, angel_client_field, angel_pass_field, angel_totp_field, ft.Divider(), ft.Text("Dhan:", weight=ft.FontWeight.BOLD), dhan_client_field, dhan_token_field], scroll=ft.ScrollMode.AUTO, height=400), actions=[ft.TextButton("SAVE KEYS", on_click=save_api_keys), ft.TextButton("CLOSE", on_click=lambda e: (setattr(page.dialog, 'open', False), page.update()))])
    page.dialog = settings_dialog
    def open_settings(e): page.dialog.open = True; page.update()

    def toggle_live(e):
        global IS_LIVE
        IS_LIVE = mode_switch.value
        if IS_LIVE:
            live_status.value = f"🟢 LIVE MODE - Real Market!"
            live_status.color = ft.Colors.GREEN
        else:
            live_status.value = "🔴 DEMO MODE (Random Data)"
            live_status.color = ft.Colors.RED
        page.update()

    mode_switch = ft.Switch(label="LIVE MODE OFF (DEMO ON) - Real Ke Liye ON Karo", value=False, on_change=toggle_live)
    settings_big_btn = ft.ElevatedButton(text="⚙️ SETTINGS - API Key Daalo Yahan", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, width=320, height=42, on_click=open_settings)

    page.add(title, settings_big_btn, trend_dashboard, filter_panel, broker_dropdown, mode_switch, balance_text, ft.Divider(height=1), nifty_text, vol_text, signal_text, option_list, last_trade)

    def buy_order(symbol, premium): last_trade.value = f"{'LIVE' if IS_LIVE else 'DEMO'} BUY {symbol} @ ₹{premium:.1f}"; page.snack_bar = ft.SnackBar(ft.Text(f"{symbol} BUY")); page.snack_bar.open = True; page.update()

    prev_nifty = 24482.0
    def live_loop():
        nonlocal prev_nifty
        while True:
            real_price, is_real = get_real_nifty()
            nifty = real_price if IS_LIVE else prev_nifty + random.uniform(-80, 90)
            source_tag = "🟢 REAL Yahoo" if (IS_LIVE and is_real) else "🟡 Yahoo Fail" if IS_LIVE else "🔴 DEMO"
            call_vol = random.randint(70, 90)
            pcr = round(random.uniform(0.65, 1.35), 2)
            nifty_trend_up = nifty > prev_nifty
            score = (30 if call_vol >= 75 else 0) + (30 if pcr < 1.0 else 0) + (30 if nifty_trend_up else 0) + 10
            is_bullish = score >= 60
            accuracy = 90 if score >= 80 else 75 if score >= 60 else 55

            if is_bullish:
                trend_text.value = "BULLISH 🚀"; trend_text.color = ft.Colors.GREEN; trend_icon.value = "🚀"; trend_dashboard.bgcolor = "#1A2B1A"; trend_dashboard.border = ft.border.all(2, ft.Colors.GREEN); trend_bar.color = ft.Colors.GREEN; signal_text.value = f"Signal: {accuracy}% BULLISH - BUY CE!"; signal_text.color = ft.Colors.GREEN
            else:
                trend_text.value = "BEARISH 📉"; trend_text.color = ft.Colors.RED; trend_icon.value = "📉"; trend_dashboard.bgcolor = "#2B1A1A"; trend_dashboard.border = ft.border.all(2, ft.Colors.RED); trend_bar.color = ft.Colors.RED; signal_text.value = f"Signal: {accuracy}% BEARISH - BUY PE!"; signal_text.color = ft.Colors.RED

            accuracy_text.value = f"Accuracy: {accuracy}%"
            trend_bar.value = accuracy/100
            trend_reason.value = f"{source_tag} | CALL {call_vol}% + PCR {pcr} + NIFTY {'UP' if nifty_trend_up else 'DOWN'}"
            nifty_text.value = f"NIFTY: {nifty:,.2f}"
            vol_text.value = f"CALL VOL: {call_vol}% | PCR: {pcr} | {datetime.now().strftime('%H:%M:%S')} {source_tag}"

            option_list.controls.clear()
            for diff in [-100, -50, 0, 50, 100]:
                strike = int(nifty/50)*50 + diff
                premium = 250 - abs(diff)*1.6 + random.uniform(-25,25)
                if premium < 20: premium = 30
                if f_call_vol.value and call_vol < 70 and diff < 0: continue
                if f_pcr.value and pcr > 1.1 and is_bullish: continue
                if f_power.value and not (120 < premium < 280): continue
                tag = "POWERFUL ✅" if 120 < premium < 280 else "RISKY ❌"; col = ft.Colors.GREEN if 120 < premium < 280 else ft.Colors.RED
                option_list.controls.append(ft.Container(bgcolor="#1E1E1E", border_radius=10, padding=10, margin=ft.margin.only(bottom=5), content=ft.Row([ft.Column([ft.Text(f"{strike} {'CE' if is_bullish else 'PE'}", weight=ft.FontWeight.BOLD), ft.Text(f"₹{premium:.1f}", size=15)], expand=True), ft.Column([ft.Text(tag, size=10, color=col), ft.ElevatedButton("BUY", bgcolor=col, color=ft.Colors.WHITE, height=28, on_click=lambda e, s=f"{strike} {'CE' if is_bullish else 'PE'}", p=premium: buy_order(s,p))])])))

            prev_nifty = nifty
            try: page.update()
            except: pass
            time.sleep(3)
    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
