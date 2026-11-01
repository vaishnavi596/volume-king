import flet as ft

def main(page: ft.Page):
    page.title = "Volume King 97 REAL"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # AAPKA PURANA WALA CODE YAHAN SE SHURU HOGA
    # BULLISH / BEARISH / Volume Spike / CALL VOL / PCR / POWERFUL Filter / Broker Login
    # Jo aapke root wale main.py me tha, wahi pura yahan paste karo
    # Neeche wala sirf sample hai taaki build fail na ho
    
    title = ft.Text("VOLUME KING 97 REAL MARKET", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    status = ft.Text("BULLISH/BEARISH + Accuracy + Broker Ready", size=14, color=ft.Colors.WHITE70)
    
    page.add(
        ft.Column([
            title,
            status,
            ft.ElevatedButton("START SCAN", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
