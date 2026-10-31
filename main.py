import flet as ft
import yfinance as yf
import random

def main(page: ft.Page):
    page.title = "Volume King"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    status = ft.Text("Volume King - 70% Volume 80-100 Bot Ready", size=20, weight=ft.FontWeight.BOLD)
    
    price_text = ft.Text("Nifty Price: Loading...", size=18)
    
    def get_price(e):
        try:
            # Nifty 50 data
            ticker = yf.Ticker("^NSEI")
            data = ticker.history(period="1d")
            if not data.empty:
                price = data['Close'].iloc[-1]
                price_text.value = f"Nifty Price: {price:.2f}"
            else:
                price_text.value = f"Demo Price: {random.randint(24000, 25000)}"
            page.update()
        except Exception as ex:
            price_text.value = f"Demo Price: {random.randint(24000, 25000)} (Offline)"
            page.update()

    btn = ft.ElevatedButton("Get Volume King Signal", on_click=get_price, bgcolor="green", color="white")

    page.add(
        ft.Column([
            status,
            price_text,
            btn
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
