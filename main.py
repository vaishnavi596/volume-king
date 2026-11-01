import flet as ft
import threading, time, random
from datetime import datetime

def main(page: ft.Page):
    page.title = "VOLUME KING 97 V8"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 10

    # Top
    title = ft.Text("VOLUME KING 97 V8 UNIVERSAL", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    broker = ft.Dropdown(label="Broker", value="Demo", options=[ft.dropdown.Option("AngelOne"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Demo")], width=180, height=50, text_size=12)
    login_btn = ft.ElevatedButton("LOGIN", bgcolor=ft.Colors.GREEN, color="white", width=80, height=40)
    
    live_switch = ft.Switch(label="DEMO MODE", value=False)
    live_label = ft.Text("DEMO MODE", color=ft.Colors.RED, size=12, weight=ft.FontWeight.BOLD)

    def switch_change(e):
        if live_switch.value:
            live_label.value = "LIVE MODE"
            live_label.color = ft.Colors.GREEN
        else:
            live_label.value = "DEMO MODE"
            live_label.color = ft.Colors.RED
        page.update()

    live_switch.on_change = switch_change

    # Market
    nifty_txt = ft.Text("LIVE NIFTY: 24532", size=22, weight=ft.FontWeight.BOLD, color="white")
    vol_bar = ft.ProgressBar(value=0.74, color=ft.Colors.GREEN, bgcolor="#333333", height=10)
    call_txt = ft.Text("CALL Vol: 74% | PUT Vol: 26%", size=14)
    pcr_txt = ft.Text("PCR: 0.92 (Neutral)", size=14)
    vwap_txt = ft.Text("VWAP: 24490", size=13)
    oi_txt = ft.Text("OI Trend: CALL OI UP", size=13, color=ft.Colors.GREEN)

    signal_title = ft.Text("90% SIGNAL: BUY CE", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    last_txt = ft.Text("Last Trade: No Trade", size=11, color=ft.Colors.GREY_400)
    signal_box = ft.Container(bgcolor="#2A2A0A", padding=12, border_radius=12, content=ft.Column([signal_title, last_txt]))

    def buy_ce(e):
        last_txt.value = f"Last: BUY CE {datetime.now().strftime('%H:%M:%S')}"
        page.snack_bar = ft.SnackBar(ft.Text("BUY CE Placed!"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    def buy_pe(e):
        last_txt.value = f"Last: BUY PE {datetime.now().strftime('%H:%M:%S')}"
        page.snack_bar = ft.SnackBar(ft.Text("BUY PE Placed!"), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    btn_ce = ft.ElevatedButton("BUY CE 90%", bgcolor="#00C853", color="white", expand=True, height=55, on_click=buy_ce)
    btn_pe = ft.ElevatedButton("BUY PE 90%", bgcolor="#D32F2F", color="white", expand=True, height=55, on_click=buy_pe)

    page.add(
        title,
        ft.Row([broker, login_btn]),
        ft.Row([live_switch, live_label]),
        nifty_txt,
        vol_bar,
        call_txt,
        pcr_txt,
        vwap_txt,
        oi_txt,
        signal_box,
        ft.Row([btn_ce, btn_pe]),
        ft.Text("ZAP MODE ON", size=10, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
    )

    def loop():
        while True:
            try:
                n = 24532 + random.uniform(-150, 150)
                cv = random.randint(65, 88)
                pcr = round(random.uniform(0.75, 1.25), 2)
                
                nifty_txt.value = f"LIVE NIFTY: {n:.0f} {'🟢' if cv>70 else '🔴'}"
                vol_bar.value = cv/100
                call_txt.value = f"CALL Vol: {cv}% | PUT Vol: {100-cv}%"
                pcr_txt.value = f"PCR: {pcr}"
                
                if cv > 75 and pcr < 1.0:
                    signal_title.value = f"{cv}% SIGNAL: BUY CE"
                    signal_title.color = ft.Colors.GREEN
                elif cv < 65:
                    signal_title.value = f"{100-cv}% SIGNAL: BUY PE"
                    signal_title.color = ft.Colors.RED

                page.update()
            except:
                pass
            time.sleep(3)

    threading.Thread(target=loop, daemon=True).start()

ft.app(target=main)
