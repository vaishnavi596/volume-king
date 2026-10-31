import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.bgcolor = ft.colors.WHITE
    
    txt = ft.Text("Volume King is Working!", size=25, color=ft.colors.BLACK, weight="bold")
    btn = ft.ElevatedButton("BOOST VOLUME", bgcolor="green", color="white", width=200)
    
    page.add(txt, btn)
    page.update()

ft.app(target=main)
