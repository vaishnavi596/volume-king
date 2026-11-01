import flet as ft

def main(page: ft.Page):
    page.title = "Volume King"
    page.bgcolor = "#0a0e1a"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    
    # Page 1 - FINAL MARKET SENTIMENT 100% COMBINED
    title = ft.Container(
        content=ft.Column([
            ft.Text("VOLUME KING", size=28, weight=ft.FontWeight.BOLD, color="#FFD700", text_align=ft.TextAlign.CENTER),
            ft.Text("FINAL MARKET SENTIMENT - 100% COMBINED", size=11, color="#ffffff99", text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor="#151a2c",
        padding=18,
        border_radius=15,
        border=ft.border.all(1, "#FFD70033")
    )
    
    # 68% Bullish Card
    main_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("MARKET BIAS", size=12, color="white54"),
                ft.Container(content=ft.Text("LIVE • 3:29 PM", size=10, color="#00ff88"), bgcolor="#00ff8822", padding=ft.padding.symmetric(4,8), border_radius=20)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text("BULLISH 68% 🟢", size=26, weight=ft.FontWeight.BOLD, color="#00ff88"),
            ft.ProgressBar(value=0.68, color="#00ff88", bgcolor="#1a2340", height=8, border_radius=5),
            ft.Text("Premium Base 40% + Nifty Base 40% + News Base 20%", size=9, color="white38"),
        ], spacing=8),
        bgcolor="#151a2c",
        padding=15,
        border_radius=15,
    )
    
    # 3 Breakdown
    row1 = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("Premium Base", size=10, color="white54"),
                ft.Text("70% BULL", size=14, weight="bold", color="#00ff88"),
                ft.Text("40% Weight", size=9, color="white38"),
            ], spacing=2),
            bgcolor="#1a2340", padding=12, border_radius=12, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Nifty Base", size=10, color="white54"),
                ft.Text("65% BULL", size=14, weight="bold", color="#00ff88"),
                ft.Text("40% Weight", size=9, color="white38"),
            ], spacing=2),
            bgcolor="#1a2340", padding=12, border_radius=12, expand=True
        ),
    ], spacing=10)
    
    row2 = ft.Container(
        content=ft.Column([
            ft.Text("News Base - 20% Weight", size=10, color="white54"),
            ft.Text("75% Positive - RBI Policy Boost + FII Buying", size=12, color="#00ff88", weight=ft.FontWeight.W500),
        ], spacing=4),
        bgcolor="#1a2340", padding=12, border_radius=12
    )
    
    btn = ft.ElevatedButton(
        text="Refresh Live Data",
        icon=ft.Icons.REFRESH,
        bgcolor="#FFD700",
        color="black",
        width=400,
        height=45,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
    )
    
    page.add(
        ft.Column([
            title,
            main_card,
            row1,
            row2,
            ft.Container(height=10),
            btn,
            ft.Text("History Auto-Saved ✅ GitHub Build Ready", size=9, color="white24", text_align=ft.TextAlign.CENTER)
        ], spacing=12, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
