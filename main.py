import flet as ft

def main(page: ft.Page):
    page.title = "Boating Trading Bot"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 800

    # LIVE DATA
    pcr_text = ft.Text("PCR: 1.15 Bullish | LIVE ●", color=ft.colors.GREEN, size=16)
    status = ft.Text("Bot STOPPED", color=ft.colors.RED)
    log = ft.Column([])

    def start_bot(e):
        status.value = "Bot RUNNING - Scanning NIFTY..."
        status.color = ft.colors.GREEN
        log.controls.append(ft.Text("Scanning NIFTY 23000 CE - Economy 85% - STRONG BUY", color=ft.colors.GREEN))
        page.update()

    def stop_bot(e):
        status.value = "Bot STOPPED"
        status.color = ft.colors.RED
        page.update()

    # Page 1 - Main
    page1 = ft.Column([
        ft.Text("Main Page - OI Auto Trading", size=20, weight="bold"),
        pcr_text,
        status,
        ft.Row([ft.ElevatedButton("START OI BOT", bgcolor=ft.colors.GREEN, color=ft.colors.WHITE, on_click=start_bot),
                ft.ElevatedButton("STOP BOT", bgcolor=ft.colors.RED, color=ft.colors.WHITE, on_click=stop_bot)]),
        log
    ])

    # Page 2 - Indicator
    page2 = ft.Column([
        ft.Text("Indicator Settings", size=20, weight="bold"),
        ft.TextField(label="Stock (HDFC, RELIANCE, TCS)", value="NIFTY"),
        ft.TextField(label="Min Economy", value="70"),
        ft.TextField(label="Max Economy", value="45"),
        ft.TextField(label="OI Filter", value="800000"),
    ])

    # Page 3 - OI Chain
    page3 = ft.Column([
        ft.Text("OI Chain - LIVE", size=20, weight="bold"),
        ft.Text("NIFTY 23000 CE - 93% STRONG BUY", color=ft.colors.GREEN),
        ft.Text("NIFTY 23100 CE - 77% BUY", color=ft.colors.GREEN),
        ft.Text("NIFTY 23200 CE - 75% BUY", color=ft.colors.GREEN),
        ft.Row([ft.ElevatedButton("BUY"), ft.ElevatedButton("SELL")])
    ])

    # Page 4 - Bot Setting
    page4 = ft.Column([
        ft.Text("Bot Settings", size=20, weight="bold"),
        ft.Switch(label="AUTO Mode", value=True),
        ft.TextField(label="Target %", value="10%"),
        ft.TextField(label="StopLoss %", value="5%"),
    ])

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Main", content=page1),
            ft.Tab(text="Indicator", content=page2),
            ft.Tab(text="OI Chain", content=page3),
            ft.Tab(text="Bot Set", content=page4),
        ],
        expand=1
    )

    page.add(tabs)

ft.app(target=main)
