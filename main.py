import flet as ft
import requests, threading, time, random

def main(page: ft.Page):
    page.title = "Boating Trading Bot"
    page.theme_mode = ft.ThemeMode.DARK
    pcr = ft.Text("PCR: 1.15 Bullish | LIVE ●", color=ft.Colors.GREEN_400, size=16, weight=ft.FontWeight.BOLD)
    status = ft.Text("Bot STOPPED 🔴", color=ft.Colors.RED_400, size=16, weight=ft.FontWeight.BOLD)
    logs = ft.Column([], spacing=4, scroll=ft.ScrollMode.AUTO)
    option_col = ft.Column(spacing=8)
    nifty_price = ft.Text("Nifty: Loading...", size=15)

    def log_msg(m,c=ft.Colors.GREEN_400):
        logs.controls.insert(0, ft.Text(f"[{time.strftime('%H:%M:%S')}] {m}", color=c, size=12))
        page.update()
    def start_bot(e):
        status.value="Bot RUNNING 🟢"; status.color=ft.Colors.GREEN_400; log_msg("Bot Started - Target 10% SL 5%"); page.update()
    def stop_bot(e):
        status.value="Bot STOPPED 🔴"; status.color=ft.Colors.RED_400; log_msg("Bot Stopped", ft.Colors.RED_400); page.update()

    tabs = ft.Tabs(tabs=[
        ft.Tab(text="Main", content=ft.Column([ft.Text("Main - OI Auto Trading", size=20, weight=ft.FontWeight.BOLD), nifty_price, pcr, status, ft.Row([ft.ElevatedButton("START OI BOT", bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=start_bot), ft.ElevatedButton("STOP BOT", bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=stop_bot)]), ft.Text("OI Chain: NIFTY 23000 CE - 93% STRONG BUY", color=ft.Colors.GREEN_400), option_col, ft.Container(bgcolor="#000", padding=10, height=150, content=logs)]) ),
        ft.Tab(text="Indicator", content=ft.Column([ft.Text("Indicator", size=20), ft.TextField(label="Stock", value="NIFTY"), ft.TextField(label="OI Filter", value="800000")]) ),
        ft.Tab(text="OI Chain", content=ft.Column([ft.Text("OI Chain LIVE", size=20), pcr, ft.Text("NIFTY 23000 CE - 93% STRONG BUY")]) ),
        ft.Tab(text="Bot Setting", content=ft.Column([ft.Text("Bot Settings", size=20), ft.Switch(label="AUTO Mode", value=True), ft.TextField(label="Target", value="10%"), status]) ),
    ], expand=1)
    page.add(tabs)

ft.app(target=main)
