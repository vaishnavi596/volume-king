import flet as ft

def main(page: ft.Page):
    page.title = "VOLUME KING"
    page.bgcolor = "#000000"
    page.add(
        ft.Text("VOLUME KING 97 - WORKING! ✅", size=24, color="green", weight="bold"),
        ft.Text("Black Fix Ho Gaya!", color="white"),
        ft.ElevatedButton("BUY CE 90%", bgcolor="green", color="white")
    )

ft.app(target=main)
