import flet as ft

def main(page: ft.Page):
    page.bgcolor = "#000000"
    page.add(
        ft.Text("VOLUME KING 97 - WORKING! ✅", size=25, color="green", weight="bold"),
        ft.Text("Black Fix Ho Gaya!", color="white", size=20),
        ft.ElevatedButton("BUY CE 90%", bgcolor="green", color="white")
    )

ft.app(target=main)
