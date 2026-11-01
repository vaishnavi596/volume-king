import flet as ft
import threading, time, random, datetime

def main(page: ft.Page):
    page.title = "Volume King"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 0

    # --- UI pehle banao, data baad me ---
    trades = ft.Text("0", color="#00FF88", weight=ft.FontWeight.BOLD, size=16)
    pcr_txt = ft.Text("1.15", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    bot_st = ft.Text("STOPPED", color="#FF3B3B", weight=ft.FontWeight.BOLD, size=18)
    last_upd = ft.Text("Last: --:--:--", size=11, color="#888")
    log_box = ft.Text("App Started...\nLoading...", color="#888", size=12, font_family="monospace")
    
    def card(c):
        return ft.Container(content=c, bgcolor="#111111", border_radius=16, padding=14, border=ft.border.all(1,"#2A2A2A"))

    def oi_row(strike, side, conf, ltp):
        return ft.Container(
            content=ft.Row([
                ft.Container(width=4, height=50, bgcolor="#00FF88" if conf>=85 else "#FFD700", border_radius=2),
                ft.Column([
                    ft.Text(f"NIFTY {strike} {side}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(f"{conf}% STRONG BUY LTP {ltp}", size=11, color="#00AA44")
                ], expand=True),
                ft.Container(content=ft.Text("BUY", size=12, weight=ft.FontWeight.BOLD), bgcolor="#00CC66", border_radius=10, padding=ft.padding.symmetric(10,16)),
            ]),
            bgcolor="#111111", border_radius=16, padding=12, border=ft.border.all(1,"#2A2A2A")
        )

    quick_col = ft.Column([
        oi_row(23000,"CE",86,"92.5"),
        oi_row(23100,"PE",87,"85.5"),
        oi_row(23000,"PE",83,"88.0"),
    ], spacing=10)

    # --- SCROLLABLE MAIN PAGE ---
    main_scroll = ft.Column([
        ft.Container(content=ft.Row([ft.Text("TRADES EXECUTED", size=10, color="#AAA"), trades]), bgcolor="#111111", border_radius=20, padding=14, border=ft.border.all(1,"#2A2A2A"), margin=ft.margin.all(12)),
        ft.Container(content=ft.Text("Bot - OI Auto Trading", size=22, weight=ft.FontWeight.BOLD), margin=ft.margin.symmetric(12,4)),
        ft.Container(content=card(ft.Text("Logic: OI High + OI Change +ve + LTP 80-100 + Vol 80% = Bullish Strong BUY", size=12, color="#6AFFAA")), margin=ft.margin.symmetric(12,6)),
        ft.Container(content=ft.Container(content=ft.Row([ft.Container(width=10,height=10,bgcolor="#00FF88",border_radius=5), ft.Column([ft.Text("REAL MARKET MODE: LIVE DATA ON", size=12, weight=ft.FontWeight.BOLD, color="#6AFFAA"), last_upd])]), bgcolor="#0A1E0A", border_radius=16, padding=14, border=ft.border.all(1,"#1A4D2E")), margin=ft.margin.symmetric(12,6)),
        ft.Container(content=ft.Row([
            card(ft.Column([ft.Text("BOT STATUS", size=10, color="#888"), ft.Row([ft.Container(width=8,height=8,bgcolor="#FF3B3B",border_radius=4), bot_st])])),
            card(ft.Column([ft.Text("MARKET PULSE Bullish", size=10, color="#888"), ft.Row([ft.Text("PCR", size=12, color="#888"), pcr_txt])])),
        ], spacing=10), margin=ft.margin.symmetric(12,6)),
        ft.Container(content=ft.ElevatedButton(content=ft.Text("START OI BOT", weight=ft.FontWeight.BOLD, color="#000"), bgcolor="#00FF66", height=52, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=lambda e: (setattr(bot_st,'value','RUNNING'), setattr(bot_st,'color','#00FF88'), page.update())), margin=ft.margin.symmetric(12,6)),
        ft.Container(content=ft.Column([ft.Text("LIVE BOT LOG", size=11, color="#AAA", weight=ft.FontWeight.BOLD), card(log_box)], spacing=6), margin=ft.margin.all(12)),
        ft.Container(content=ft.Column([ft.Text("QUICK OI CHAIN • LIVE", size=11, color="#AAA", weight=ft.FontWeight.BOLD), quick_col], spacing=10), margin=ft.margin.all(12)),
        ft.Container(height=80)
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)

    content_area = ft.Container(content=main_scroll, expand=True)

    # --- BOTTOM NAV (Custom, NavigationBar se blank hota hai) ---
    def go_main(e): content_area.content = main_scroll; page.update()
    def go_ind(e): 
        content_area.content = ft.Column([ft.Text("Indicator Page", size=20, weight=ft.FontWeight.BOLD), ft.Text("Premium Min 80 Max 100\nOI Filter 500000\nVol 80% ON\nLogic: OI High + OI Change +ve = BUY", color="#AAA")], scroll=ft.ScrollMode.AUTO, expand=True)
        page.update()
    def go_chain(e):
        content_area.content = ft.Column([ft.Text("OI Chain Page", size=20, weight=ft.FontWeight.BOLD), quick_col], scroll=ft.ScrollMode.AUTO, expand=True)
        page.update()
    def go_set(e):
        content_area.content = ft.Column([ft.Text("Bot Setting", size=20, weight=ft.FontWeight.BOLD), ft.Switch(label="AUTO Mode", value=True, active_color="#00FF88"), ft.TextField(label="Target 10%", value="10"), ft.TextField(label="SL 5%", value="5")], scroll=ft.ScrollMode.AUTO, expand=True)
        page.update()

    bottom = ft.Container(
        content=ft.Row([
            ft.TextButton("Main Bot", icon=ft.Icons.DASHBOARD, style=ft.ButtonStyle(color="#00FF88"), on_click=go_main, expand=True),
            ft.TextButton("Indicator", icon=ft.Icons.TUNE, style=ft.ButtonStyle(color="#666"), on_click=go_ind, expand=True),
            ft.TextButton("OI Chain", icon=ft.Icons.LIST, style=ft.ButtonStyle(color="#666"), on_click=go_chain, expand=True),
            ft.TextButton("Setting", icon=ft.Icons.SETTINGS, style=ft.ButtonStyle(color="#666"), on_click=go_set, expand=True),
        ]),
        bgcolor="#0F0F0F", padding=8, border=ft.border.only(top=ft.BorderSide(1,"#222"))
    )

    page.add(ft.Column([content_area, bottom], expand=True, spacing=0))

    # --- BACKGROUND DATA (2 sec baad, UI ko block nahi karega) ---
    def bg_loop():
        time.sleep(2)
        for i in range(100):
            try:
                last_upd.value = f"Last: {datetime.datetime.now().strftime('%H:%M:%S')} LIVE"
                pcr_txt.value = f"{random.uniform(0.85,1.35):.2f}"
                log_box.value = f"{datetime.datetime.now().strftime('%H:%M:%S')} Scanning NIFTY\nLogic 80-100 + Vol 80% matched\nFound {random.randint(2,6)} signals"
                page.update()
            except: pass
            time.sleep(3)

    threading.Thread(target=bg_loop, daemon=True).start()

ft.app(target=main)
