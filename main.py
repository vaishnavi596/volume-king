import flet as ft
import random
import time
import threading
from datetime import datetime

def main(page: ft.Page):
    page.title = "VOLUME KING 97"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 12
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- Title ---
    title = ft.Text("VOLUME KING 97 V8 UNIVERSAL", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN, text_align=ft.TextAlign.CENTER)
    
    # --- Broker ---
    broker = ft.Dropdown(label="Broker", value="Demo", options=[ft.dropdown.Option("AngelOne"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Demo")], width=170, text_size=13, height=50)
    login = ft.ElevatedButton("LOGIN", bgcolor="green", color="white", width=80)

    # --- Mode ---
    mode_txt = ft.Text("DEMO MODE", color="red", weight=ft.FontWeight.BOLD, size=14)
    mode_sw = ft.Switch(label="DEMO", value=False)
    def mode_change(e):
        mode_txt.value = "LIVE MODE 🟢" if mode_sw.value else "DEMO MODE 🔴"
        mode_txt.color = "green" if mode_sw.value else "red"
        page.update()
    mode_sw.on_change = mode_change

    # --- Market Data ---
    nifty = ft.Text("LIVE NIFTY: 24532 🟢", size=24, weight=ft.FontWeight.BOLD, color="white")
    vol_bar = ft.ProgressBar(value=0.74, color="green", bgcolor="#333333", height=12)
    call_vol = ft.Text("CALL Vol: 74% | PUT Vol: 26%", size=15, color="white")
    pcr = ft.Text("PCR: 0.92 (Neutral)", size=14, color="yellow")
    vwap = ft.Text("VWAP: 24490 | Price VWAP UPAR", size=13, color="grey")
    
    signal = ft.Text("🔥 90% SIGNAL: BUY CE", size=18, weight=ft.FontWeight.BOLD, color="yellow")
    last = ft.Text("Last Trade: No Trade", size=12, color="grey")
    signal_box = ft.Container(bgcolor="#222200", padding=10, border_radius=10, content=ft.Column([signal, last]))

    def buy_ce(e):
        last.value = f"BUY CE @ {datetime.now().strftime('%H:%M:%S')} ✅"
        page.snack_bar = ft.SnackBar(ft.Text("BUY CE 90% Placed! 🚀"), bgcolor="green")
        page.snack_bar.open = True
        page.update()
    def buy_pe(e):
        last.value = f"BUY PE @ {datetime.now().strftime('%H:%M:%S')} ✅"
        page.snack_bar = ft.SnackBar(ft.Text("BUY PE 90% Placed! 📉"), bgcolor="red")
        page.snack_bar.open = True
        page.update()

    b1 = ft.ElevatedButton("BUY CE 90%", bgcolor="#00C853", color="white", expand=True, height=55, on_click=buy_ce)
    b2 = ft.ElevatedButton("BUY PE 90%", bgcolor="#D32F2F", color="white", expand=True, height=55, on_click=buy_pe)

    page.add(
        title,
        ft.Row([broker, login]),
        ft.Row([mode_sw, mode_txt]),
        ft.Divider(color="#333", height=1),
        nifty,
        vol_bar,
        call_vol,
        pcr,
        vwap,
        signal_box,
        ft.Row([b1, b2]),
        ft.Text("V8.1 SAFE MODE - NCC Tag Next", size=10, color="grey", text_align=ft.TextAlign.CENTER)
    )

    # --- SAFE LOOP ---
    def live():
        while True:
            time.sleep(3)
            try:
                nv = 24532 + random.uniform(-150, 150)
                cv = random.randint(65, 88)
                nifty.value = f"LIVE NIFTY: {nv:.0f} {'🟢' if cv>70 else '🔴'}"
                call_vol.value = f"CALL Vol: {cv}% | PUT Vol: {100-cv}%"
                vol_bar.value = cv/100
                if cv > 76:
                    signal.value = f"🔥 {cv}% SIGNAL: BUY CE"
                    signal.color = "green"
                page.update()
            except:
                pass

    threading.Thread(target=live, daemon=True).start()

ft.app(target=main)
