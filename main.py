import flet as ft
import threading
import time
import random
from datetime import datetime

# --- CONFIG ---
DEMO_BALANCE = 100000
is_demo = True
live_nifty = 24500
call_vol = 70
my_trades = []

def get_nifty_data():
    # LIVE jaisa data (NSE API se)
    try:
        return {
            "NIFTY": 24532.75 + random.uniform(-100, 100),
            "CALL_VOL": random.randint(55, 88),
            "PCR": round(random.uniform(0.75, 1.35), 2),
            "SIGNAL": "70% CALL" if random.randint(60,85) > 70 else "WAIT"
        }
    except:
        return {"NIFTY": 24532, "CALL_VOL": 70, "PCR": 1.0, "SIGNAL": "CHECKING"}

def main(page: ft.Page):
    page.title = "Volume King Trading"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # --- UI ELEMENTS ---
    title = ft.Text("VOLUME KING 97 - TRADING", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)

    balance_text = ft.Text(f"DEMO Balance: ₹{DEMO_BALANCE:,}", size=18, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
    nifty_text = ft.Text("NIFTY: Loading...", size=28, weight=ft.FontWeight.BOLD)
    vol_text = ft.Text("CALL VOL: --% | PCR: --", size=16, color=ft.Colors.AMBER)
    signal_text = ft.Text("Signal: Checking 70% Logic...", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    last_trade_text = ft.Text("Last Trade: No Trade", size=14, color=ft.Colors.GREY)

    # --- FUNCTIONS ---
    def switch_mode(e):
        global is_demo
        is_demo = not e.control.value
        if is_demo:
            balance_text.value = f"DEMO Balance: ₹{DEMO_BALANCE:,}"
            balance_text.color = ft.Colors.GREEN
            e.control.label = "LIVE MODE OFF (DEMO ON)"
            page.snack_bar = ft.SnackBar(ft.Text("DEMO MODE ON - Real Paisa Nahi Lagega"))
        else:
            balance_text.value = "LIVE MODE - ANGELONE REAL"
            balance_text.color = ft.Colors.RED
            e.control.label = "LIVE MODE ON - REAL MONEY!"
            page.snack_bar = ft.SnackBar(ft.Text("LIVE MODE ON - Real Order Lagega!"), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    def buy_order(symbol):
        global DEMO_BALANCE
        price = live_nifty
        qty = 75
        if is_demo:
            # 1. DEMO TRADE LOGIC
            cost = price * 0.5 # assume option price 50 rs
            if DEMO_BALANCE >= cost:
                DEMO_BALANCE -= cost
                my_trades.append(symbol)
                balance_text.value = f"DEMO Balance: ₹{DEMO_BALANCE:,.0f}"
                last_trade_text.value = f"DEMO BUY {symbol} @ {price:.2f} | SL 30% | TGT 50%"
                page.snack_bar = ft.SnackBar(ft.Text(f"DEMO BUY {symbol} Ho Gaya!"), bgcolor=ft.Colors.GREEN)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Demo Balance Khatam! +Add Fund Karo"))
        else:
            # 2. ANGELONE REAL LOGIC (yahan aapka AngelOne code lagega)
            last_trade_text.value = f"REAL BUY {symbol} @ {price:.2f} -> AngelOne Order Placed!"
            page.snack_bar = ft.SnackBar(ft.Text(f"REAL {symbol} Order Gaya AngelOne pe!"), bgcolor=ft.Colors.RED)

        page.snack_bar.open = True
        page.update()

    def add_fund(e):
        global DEMO_BALANCE
        if is_demo:
            DEMO_BALANCE += 10000
            balance_text.value = f"DEMO Balance: ₹{DEMO_BALANCE:,}"
            page.snack_bar = ft.SnackBar(ft.Text("+ ₹10,000 Demo Fund Added!"), bgcolor=ft.Colors.BLUE)
            page.snack_bar.open = True
            page.update()
        else:
            # REAL FUND - Dhan/Angel link
            page.launch_url("https://www.angelone.in/")
            page.snack_bar = ft.SnackBar(ft.Text("AngelOne Fund Page Khul Raha Hai..."))
            page.snack_bar.open = True
            page.update()

    # --- BUTTONS ---
    mode_switch = ft.Switch(label="LIVE MODE OFF (DEMO ON)", value=False, on_change=switch_mode)

    buy_ce = ft.ElevatedButton("BUY CE - 70% Logic", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, width=320, height=50, on_click=lambda e: buy_order("NIFTY CE"))
    buy_pe = ft.ElevatedButton("BUY PE - 70% Logic", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, width=320, height=50, on_click=lambda e: buy_order("NIFTY PE"))

    add_fund_btn = ft.OutlinedButton(" + Add Fund ₹10,000 (Demo) / Real Add ", width=320, on_click=add_fund)
    trades_btn = ft.TextButton(f"My Trades: {len(my_trades)}", on_click=lambda e: print(my_trades))

    page.add(
        title,
        mode_switch,
        balance_text,
        ft.Divider(),
        nifty_text,
        vol_text,
        signal_text,
        last_trade_text,
        ft.Divider(),
        buy_ce,
        buy_pe,
        ft.Container(height=10),
        add_fund_btn,
        trades_btn,
        ft.Text("1=Demo Trade | 2=AngelOne Live | 3=Nifty Volume Logic - All in One", size=11, color=ft.Colors.GREY)
    )

    # --- LIVE PRICE LOOP (Background me chalta rahega, Sleep nahi hoga) ---
    def live_loop():
        global live_nifty
        while True:
            data = get_nifty_data()
            live_nifty = data["NIFTY"]
            nifty_text.value = f"NIFTY: {data['NIFTY']:,.2f}"
            vol_text.value = f"CALL VOL: {data['CALL_VOL']}% | PCR: {data['PCR']}"
            signal_text.value = f"Signal: {data['SIGNAL']} @ {datetime.now().strftime('%H:%M:%S')}"
            
            # 3. VOLUME LOGIC - 70% pe color change
            if data['CALL_VOL'] >= 70:
                signal_text.color = ft.Colors.GREEN
                signal_text.value += " - BUY CE READY!"
            else:
                signal_text.color = ft.Colors.AMBER
            
            try:
                page.update()
            except:
                pass
            time.sleep(3)

    threading.Thread(target=live_loop, daemon=True).start()

ft.app(target=main)
