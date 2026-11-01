import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.bgcolor = "#000000"
    page.add(
        ft.Text("VOLUME KING WORKING! 🔊", size=30, color="green", weight="bold"),
        ft.Text("Agar ye dikh raha hai to APK sahi hai", color="white"),
        ft.ElevatedButton("BOOST 150% 🔊", bgcolor="green", color="white", width=300, height=50),
        ft.Slider(value=50, min=0, max=150),
    )

ft.app(target=main)
