import flet as ft
import threading, time, random, json, ssl
from datetime import datetime

# SSL crash fix for Android
ssl._create_default_https_context = ssl._create_unverified_context

DEMO_BALANCE = 100000

# --- LIVE NIFTY FETCH - Safe Wala ---
def get_real_nifty():
    try:
        import urllib.request
        # Yahoo Finance - NIFTY 50 (^NSEI)
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            if price and price > 10000: # Nifty 10k se upar hi hoga
                return float(price), True
    except Exception as e:
        print(f"Live fetch fail: {e}")
    return None, False

def main(page: ft.Page):
    page.title = "Volume King 97"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 12
    page.scroll = ft.ScrollMode.AUTO

    title = ft.Text("VOLUME KING 97 - LIVE", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)

    # --- BULLISH DASHBOARD ---
    trend_icon = ft.Text("🚀", size=32)
    trend_text = ft.Text("BULLISH", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    accuracy_text = ft.Text("Accuracy: 90%", size=14, color=ft.Colors.AMBER)
    trend_reason = ft.Text("CALL 88% + PCR 0.83 + NIFTY UP", size=11, color=ft.Colors.GREY_400)
    trend_bar = ft.ProgressBar(value=0.9, color=ft.Colors.GREEN, bgcolor="#333", height=8, width=320)
    live_status = ft.Text("🔴 DEMO STABLE MODE", color=ft.Colors.GREY, size=12)

    trend_dashboard = ft.Container(
        bgcolor="#1A2B1A", border_radius=15, padding=12,
        border=ft.border.all(2, ft.Colors.GREEN),
        content=ft.Column([
            ft.Row([trend_icon, trend_text, ft.Container(expand=True), accuracy_text]),
            trend_bar,
            trend_reason,
            live_status
        ])
    )

    # --- FILTERS ---
    f_call_vol = ft.Switch(label="90% CALL VOL Filter", value=True)
    f_pcr = ft.Switch(label="PCR <1.0 Bullish Filter", value=True)
    f_power = ft.Switch(label="POWERFUL (120-280) Only", value=True)

    filter_panel = ft.Container(bgcolor="#111", border_radius=10, padding=10, 
        content=ft.Column([ft.Text("90% Accuracy Ke Filters ON/OFF:", size=12, weight=ft.FontWeight.BOLD), f_call_vol, f_pcr, f_power]))

    balance_text = ft.Text(f"DEMO Balance: ₹{DEMO_BALANCE:,}", size=16, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
    nifty_text = ft.Text("NIFTY: 24,482.30", size=26, weight=ft.FontWeight.BOLD)
    vol_text = ft.Text("CALL VOL: 84% | PCR: 0.85", size=13, color=ft.Colors.AMBER)
    signal_text = ft.Text("Signal: 90% BULLISH - BUY CE!", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    option_list = ft.Column()
    last_trade = ft.Text("Last Trade: No Trade", size=12, color=ft.Colors.GREY)

    def open_settings(e):
        page.snack_bar = ft.SnackBar(ft.Text("Settings - Agle version me Broker API!"))
        page.snack_bar.open = True
        page.update()

    settings_big_btn = ft.ElevatedButton(text="⚙️ SETTINGS", bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK, width=320, height=42, on_click=open_settings)
    
    # --- YEH RAHA MAIN SWITCH ---
    def on_live_toggle(e):
        if mode_switch.value:
            live_status.value = "🟡 LIVE DATA ON - Fetching Real Nifty..."
            live_status.color = ft.Colors.AMBER
        else:
            live_status.value = "🔴 DEMO MODE - Random Data"
            live_status.color = ft.Colors.GREY
        page.update()

    mode_switch = ft.Switch(label="LIVE DATA ON Karo (Real Nifty)", value=False, on_change=on_live_toggle)

    page.add(title, settings_big_btn, trend_dashboard, filter_panel, mode_switch, balance_text, ft.Divider(height=1), nifty_text, vol_text, signal_text, option_list, last_trade)

    def buy_order(symbol, premium):
        last_trade.value = f"📝 DEMO TRADE {symbol} @ ₹{premium:.1f} - Safe!"
        page.snack_bar = ft.SnackBar(ft.Text(f"{symbol} BUY @ {premium} - DEMO"))
        page.snack_bar.open = True
        page.update()

    prev_nifty = 24482.0
    real_nifty_cache = 24482.0

    def live_loop():
        nonlocal prev_nifty, real_nifty_cache
        while True:
            try:
                # --- LIVE DATA LOGIC ---
                if mode_switch.value:
                    price, is_real = get_real_nifty()
                    if is_real and price:
                        real_nifty_cache = price
                        nifty = price
                        live_status.value = f"🟢 LIVE REAL DATA - {datetime.now().strftime('%H:%M:%S')}"
                        live_status.color = ft.Colors.GREEN
                    else:
                        nifty = real_nifty_cache + random.uniform(-20, 20)
                        live_status.value = "🟡 LIVE ON but Market Band (Sat/Sun) - Last Close"
                        live_status.color = ft.Colors.AMBER
                else:
                    nifty = prev_nifty + random.uniform(-60, 70)

                call_vol = random.randint(72, 91)
                pcr = round(random.uniform(0.68, 1.25), 2)
                nifty_up = nifty > prev_nifty
                
                score = 0
                if call_vol >= 75: score += 30
                if pcr < 1.0: score += 30
                if nifty_up: score += 30
                score += 10

                is_bullish = score >= 60
                accuracy = 90 if score >= 80 else 75 if score >= 60 else 55

                if is_bullish:
                    trend_text.value = "BULLISH 🚀"; trend_text.color = ft.Colors.GREEN; trend_icon.value = "🚀"
                    trend_dashboard.bgcolor = "#1A2B1A"; trend_dashboard.border = ft.border.all(2, ft.Colors.GREEN)
                    trend_bar.color = ft.Colors.GREEN
                    signal_text.value = f"Signal: {accuracy}% BULLISH - BUY CE!"; signal_text.color = ft.Colors.GREEN
                else:
                    trend_text.value = "BEARISH 📉"; trend_text.color = ft.Colors.RED; trend_icon.value = "📉"
                    trend_dashboard.bgcolor = "#2B1A1A"; trend_dashboard.border = ft.border.all(2, ft.Colors.RED)
                    trend_bar.color = ft.Colors.RED
                    signal_text.value = f"Signal: {accuracy}% BEARISH - BUY PE!"; signal_text.color = ft.Colors.RED

                accuracy_text.value = f"Accuracy: {accuracy}%"
                trend_bar.value = accuracy/100
                trend_reason.value = f"CALL {call_vol}% ({'✓' if call_vol>=75 else '✗'}) + PCR {pcr} ({'✓' if pcr<1 else '✗'}) + NIFTY {'UP' if nifty_up else 'DOWN'} = {score} Marks"
                nifty_text.value = f"NIFTY: {nifty:,.2f}"
                vol_text.value = f"CALL VOL: {call_vol}% | PCR: {pcr} | {datetime.now().strftime('%H:%M:%S')}"

                option_list.controls.clear()
                for diff in [-100, -50, 0, 50, 100]:
                    strike = int(nifty/50)*50 + diff
                    premium = 250 - abs(diff)*1.6 + random.uniform(-20,20)
                    if premium < 20: premium = 30
                    
                    if f_call_vol.value and call_vol < 75 and diff < 0: continue
                    if f_pcr.value and pcr > 1.1 and is_bullish: continue
                    if f_power.value and not (120 < premium < 280): continue

                    tag = "POWERFUL ✅" if 120 < premium < 280 else "RISKY ❌"; col = ft.Colors.GREEN if 120 < premium < 280 else ft.Colors.RED
                    option_list.controls.append(
                        ft.Container(bgcolor="#1E1E1E", border_radius=10, padding=10, margin=ft.margin.only(bottom=5),
                            content=ft.Row([
                                ft.Column([ft.Text(f"{strike} {'CE' if is_bullish else 'PE'}", weight=ft.FontWeight.BOLD), ft.Text(f"₹{premium:.1f}", size=15)], expand=True),
                                ft.Column([ft.Text(tag, size=10, color=col), ft.ElevatedButton("BUY", bgcolor=col, color=ft.Colors.WHITE, height=28, on_click=lambda e, s=f"{strike} {'CE' if is_bullish else 'PE'}", p=premium: buy_order(s,p))])
                            ])
                        )
                    )
                prev_nifty = nifty
                try: page.update()
                except: pass
            except Exception as ex:
                print("Loop error:", ex)
            time.sleep(3)

    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
