import flet as ft
import random

def main(page: ft.Page):
    page.title = "Bot King Trade"
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # --- Texts ---
    nifty_txt = ft.Text("Nifty: 23053.10", size=21, color="white")
    bank_txt = ft.Text("BankNifty: 54686.95", size=21, color="white")
    sensex_txt = ft.Text("Sensex: 74459.53", size=21, color="white")
    vol_txt = ft.Text("Wait - Volume 78%", size=24, weight=ft.FontWeight.BOLD, color="#FFA500")

    def refresh_click(e):
        nifty_txt.value = f"Nifty: {random.uniform(23000, 23200):.2f} (Live)"
        bank_txt.value = f"BankNifty: {random.uniform(54500, 54900):.2f} (Live)"
        sensex_txt.value = f"Sensex: {random.uniform(74300, 74700):.2f} (Live)"
        page.update()

    def signal_click(e):
        v = random.randint(70, 98)
        if v >= 80:
            vol_txt.value = f"BUY Signal - Volume {v}%\n- GO!"
            vol_txt.color = "#4CAF50"
        else:
            vol_txt.value = f"Wait - Volume {v}%"
            vol_txt.color = "#FFA500"
        page.update()

    # --- UI ---
    top_content = ft.Column([
        ft.Text("Bot King Trade", size=28, weight=ft.FontWeight.BOLD, color="white"),
        ft.Text("70% Volume 80-100 Bot Ready", size=15, color="#4CAF50"),
        ft.Divider(color="#333333", height=15),
        nifty_txt,
        bank_txt,
        sensex_txt,
        ft.ElevatedButton("Refresh Live Price", bgcolor="#4CAF50", color="white", on_click=refresh_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20))),
        ft.Divider(color="#333333", height=25),
        vol_txt,
        ft.ElevatedButton("Get Volume Signal", width=400, height=52, bgcolor="#2196F3", color="white", on_click=signal_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25))),
    ], spacing=18)

    main_area = ft.Container(content=top_content, padding=20, expand=True)

    # --- Bottom Nav - Same as your photo ---
    nav = ft.NavigationBar(
        bgcolor="#1E1E1E",
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ft.NavigationBarDestination(icon=ft.Icons.CHECK, label="Indicator"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY, label="Bot"),
        ]
    )

    page.add(
        ft.Column([main_area, nav], expand=True, spacing=0)
    )

ft.app(target=main)
