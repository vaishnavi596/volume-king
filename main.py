import flet as ft
import threading, time, random, json
from datetime import datetime

DEMO_BALANCE = 100000
is_demo = True

api_config = {
    "broker": "Demo", "angel_api_key": "", "angel_client": "",
    "angel_pass": "", "angel_totp": "", "dhan_client": "", "dhan_token": ""
}

def main(page: ft.Page):
    page.title = "Volume King Trading"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    try:
        saved = page.client_storage.get("api_config")
        if saved:
            api_config.update(json.loads(saved))
    except:
        pass

    title = ft.Text("VOLUME KING 97 - TRADING", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    
    broker_dropdown = ft.Dropdown(
        label="Broker Choose Karo",
        value=api_config["broker"],
        options=[ft.dropdown.Option("Demo"), ft.dropdown.Option("AngelOne"), ft.dropdown.Option("Dhan"), ft.dropdown.Option("Navia")],
        width=320,
        on_change=lambda e: page.client_storage.set("api_config", json.dumps(api_config))
    )

    balance_text = ft.Text(f"DEMO Balance: ₹{DEMO_BALANCE:,}", size=18, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
    nifty_text = ft.Text("NIFTY: 24,386.69", size=28, weight=ft.FontWeight.BOLD)
    vol_text = ft.Text("CALL VOL: 70% | PCR: 0.76", size=14, color=ft.Colors.AMBER)
    signal_text = ft.Text("Signal: 70% CALL - BUY CE Recommended!", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    option_list = ft.Column()
    last_trade = ft.Text("Last Trade: No Trade", size=13, color=ft.Colors.GREY)

    angel_key_field = ft.TextField(label="AngelOne API Key", value=api_config["angel_api_key"], width=320)
    angel_client_field = ft.TextField(label="AngelOne Client Code", value=api_config["angel_client"], width=320)
    angel_pass_field = ft.TextField(label="AngelOne Password/PIN", password=True, value=api_config["angel_pass"], width=320)
    angel_totp_field = ft.TextField(label="AngelOne TOTP Secret", value=api_config["angel_totp"], width=320)
    dhan_client_field = ft.TextField(label="Dhan Client ID", value=api_config["dhan_client"], width=320)
    dhan_token_field = ft.TextField(label="Dhan Access Token", value=api_config["dhan_token"], width=320)

    def save_api_keys(e):
        api_config["angel_api_key"] = angel_key_field.value
        api_config["angel_client"] = angel_client_field.value
        api_config["angel_pass"] = angel_pass_field.value
        api_config["angel_totp"] = angel_totp_field.value
        api_config["dhan_client"] = dhan_client_field.value
        api_config["dhan_token"] = dhan_token_field.value
        page.client_storage.set("api_config", json.dumps(api_config))
        page.dialog.open = False
        page.snack_bar = ft.SnackBar(ft.Text("API Keys Save Ho Gaye! ✅"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    settings_dialog = ft.AlertDialog(
        title=ft.Text("API Keys Setting"),
        content=ft.Column([
            ft.Text("AngelOne:", weight=ft.FontWeight.BOLD),
            angel_key_field, angel_client_field, angel_pass_field, angel_totp_field,
            ft.Divider(),
            ft.Text("Dhan:", weight=ft.FontWeight.BOLD),
            dhan_client_field, dhan_token_field,
        ], scroll=ft.ScrollMode.AUTO, height=400),
        actions=[ft.TextButton("SAVE KEYS", on_click=save_api_keys), ft.TextButton("CLOSE", on_click=lambda e: (setattr(page.dialog, 'open', False), page.update()))]
    )
    page.dialog = settings_dialog

    def open_settings(e):
        page.dialog.open = True
        page.update()

    def buy_order(symbol, premium):
        global DEMO_BALANCE
        power_tag = "POWERFUL ✅" if 120 < premium < 280 else "RISKY ❌"
        if broker_dropdown.value == "Demo" or is_demo:
            DEMO_BALANCE -= premium
            balance_text.value = f"DEMO Balance: ₹{DEMO_BALANCE:,.0f}"
            last_trade.value = f"DEMO BUY {symbol} @ ₹{premium:.2f} [{power_tag}]"
            page.snack_bar = ft.SnackBar(ft.Text(f"{symbol} BUY @ {premium}"), bgcolor=ft.Colors.GREEN)
        else:
            last_trade.value = f"REAL BUY {symbol} @ ₹{premium:.2f} -> {broker_dropdown.value}!"
            page.snack_bar = ft.SnackBar(ft.Text(f"REAL Order {broker_dropdown.value} pe!"))
        page.snack_bar.open = True
        page.update()

    mode_switch = ft.Switch(label="LIVE MODE OFF (DEMO ON)", value=False)
    
    settings_big_btn = ft.ElevatedButton(
        text="⚙️ SETTINGS - API Key Daalo Yahan",
        bgcolor=ft.Colors.AMBER,
        color=ft.Colors.BLACK,
        width=320,
        height=45,
        on_click=open_settings
    )

    page.add(
        title,
        settings_big_btn,
        broker_dropdown,
        mode_switch,
        balance_text,
        ft.Divider(),
        nifty_text,
        vol_text,
        signal_text,
        option_list,
        last_trade,
        ft.Divider(),
        ft.ElevatedButton("⚙️ SETTINGS Dobara Kholne Ke Liye", on_click=open_settings, width=320)
    )

    def live_loop():
        while True:
            nifty = 24386 + random.uniform(-150, 150)
            call_vol = random.randint(55, 88)
            strikes = []
            for diff in [-150, -100, -50, 0, 50]:
                strike = int(nifty/50)*50 + diff
                premium = 250 - abs(diff)*1.8 + random.uniform(-20,20)
                if premium < 20: premium = 20+random.uniform(5,20)
                if 120 < premium < 280:
                    tag, color = "POWERFUL ✅ SLOW DECAY", ft.Colors.GREEN
                elif premium < 80:
                    tag, color = "RISKY ❌ Jaldi Galega", ft.Colors.RED
                else:
                    tag, color = "OK", ft.Colors.AMBER
                strikes.append((strike, premium, tag, color))

            nifty_text.value = f"NIFTY: {nifty:,.2f}"
            vol_text.value = f"CALL VOL: {call_vol}% | PCR: {random.uniform(0.7,1.3):.2f} | {datetime.now().strftime('%H:%M:%S')}"
            signal_text.value = f"Signal: {'70% CALL - BUY CE Recommended!' if call_vol>=70 else f'WAIT - {call_vol}%'}"

            option_list.controls.clear()
            for strike, prem, tag, col in strikes:
                option_list.controls.append(
                    ft.Container(
                        bgcolor="#1E1E1E", border_radius=10, padding=10, margin=ft.margin.only(bottom=5),
                        content=ft.Row([
                            ft.Column([ft.Text(f"{strike} CE", weight=ft.FontWeight.BOLD), ft.Text(f"₹{prem:.1f}", size=16)], expand=True),
                            ft.Column([ft.Text(tag, size=11, color=col), ft.ElevatedButton("BUY", bgcolor=col, color=ft.Colors.WHITE, height=30, on_click=lambda e, s=f"{strike} CE", p=prem: buy_order(s,p))])
                        ])
                    )
                )
            try: page.update()
            except: pass
            time.sleep(4)
    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
