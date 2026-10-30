import flet as ft

def main(page: ft.Page):
    page.title = "VOLUME KING V10"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080A12"
    page.add(ft.Text("VOLUME KING V10 ULTIMATE", size=24, weight=ft.FontWeight.BOLD, color="white"))
    page.add(ft.Text("NIFTY 24500 CE @ 124.5 -> TARGET 165.8", size=18, color="#00E676"))
    page.add(ft.ElevatedButton("BUY CE 24500 CE", bgcolor="#00E676", color="white"))

ft.app(target=main)
