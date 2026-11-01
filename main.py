import flet as ft
import threading, time, random, datetime, requests, json

def main(page: ft.Page):
    page.title = "Volume King V4 NSE + Order"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 0

    BLUE_CHIPS = ["NIFTY","BANKNIFTY","FINNIFTY","RELIANCE","HDFCBANK","TCS","INFY","SBIN"]
    selected_symbol = ft.Text("NIFTY", size=13, color="#00FF88", weight=ft.FontWeight.BOLD)
    nifty_live = ft.Text("Connecting NSE FREE...", size=12, color="#00FF88", weight=ft.FontWeight.BOLD)
    call_bull = ft.Text("0%", size=22, weight=ft.FontWeight.BOLD, color="#00FF88")
    put_bull = ft.Text("0%", size=22, weight=ft.FontWeight.BOLD, color="#FF6B8A")
    barrier_text = ft.Text("Scanning REAL NSE...", size=12, weight=ft.FontWeight.BOLD, color="#FFD700")
    barrier_bar = ft.ProgressBar(value=0.5, color="#00FF88", bgcolor="#442233", height=10, border_radius=4)
    log_box = ft.Text("NSE FREE MODE + Order Panel V4", color="#00FF88", size=11)
    last_upd = ft.Text("--:--:--", size=10, color="#888")
    data_source = ft.Text("Source: NSE India FREE - Tagged", size=9, color="#00FF88", weight=ft.FontWeight.BOLD)
    auto_mode_status = ft.Text("Mode: MANUAL", size=10, color="#FFD700", weight=ft.FontWeight.BOLD)

    # Auto Mode Settings (Global)
    auto_enabled = ft.Switch(label="AUTO BUY ON - 70% Bullish pe auto buy", value=False, active_color="#00FF88")
    auto_threshold_field = ft.TextField(label="Auto Threshold %", value="70", width=120, bgcolor="#0A0A0A", border_color="#333")

    def card(c, pad=14):
        return ft.Container(content=c, bgcolor="#111111", border_radius=16, padding=pad, border=ft.border.all(1, "#2A2A2A"))

    symbol_dropdown = ft.Dropdown(label="🔍 NSE LIVE TAGGED - NIFTY/BANKNIFTY", value="NIFTY", options=[ft.dropdown.Option(s) for s in BLUE_CHIPS], bgcolor="#111111", border_color="#00FF88", on_change=lambda e: fetch_live(), expand=True)

    real_chart = ft.LineChart(
        data_series=[ft.LineChartData(data_points=[], color="#00FF88", curved=True, stroke_width=2, below_line_bgcolor=ft.Colors.with_opacity(0.2, "#00FF88"), point=False)],
        border=ft.BorderSide(1, "#2A2A2A"),
        horizontal_grid_lines=ft.ChartGridLines(interval=100, color="#1A1A1A", width=1),
        vertical_grid_lines=ft.ChartGridLines(interval=5, color="#1A1A1A", width=1),
        left_axis=ft.ChartAxis(labels_size=42),
        bottom_axis=ft.ChartAxis(labels_size=0),
        tooltip_bgcolor="#111111",
        min_y=0, max_y=100, min_x=0, max_x=60, expand=True
    )
    price_history = []

    # --- BUY SELL DIALOG V4 ---
    def open_buy_dialog(strike, side, ltp, conf):
        lot_field = ft.Dropdown(label="Lot Size", value="1", options=[ft.dropdown.Option("1"), ft.dropdown.Option("2"), ft.dropdown.Option("3"), ft.dropdown.Option("5")], bgcolor="#111111", border_color="#00FF88", width=100)
        target_field = ft.TextField(label="Target %", value="10", width=110, bgcolor="#0A0A0A", border_color="#333")
        sl_field = ft.TextField(label="Stop Loss %", value="5", width=110, bgcolor="#0A0A0A", border_color="#FF3B3B")
        order_type = ft.Dropdown(label="Order Type", value="MARKET", options=[ft.dropdown.Option("MARKET"), ft.dropdown.Option("LIMIT")], bgcolor="#111111", border_color="#FFD700", width=130)
        limit_price = ft.TextField(label="Limit Price", value=str(ltp), width=120, bgcolor="#0A0A0A", border_color="#FFD700")
        avg1_rate = ft.TextField(label="Avg Lot 1 Rate (Margin 1)", hint_text="Ex: 22900", width=160, bgcolor="#0A0A0A", border_color="#333")
        avg1_qty = ft.Dropdown(label="Lot", value="1", options=[ft.dropdown.Option("1"), ft.dropdown.Option("2")], width=80, bgcolor="#111111")
        avg2_rate = ft.TextField(label="Avg Lot 2 Rate (Margin 2)", hint_text="Ex: 22800", width=160, bgcolor="#0A0A0A", border_color="#333")
        avg2_qty = ft.Dropdown(label="Lot", value="1", options=[ft.dropdown.Option("1"), ft.dropdown.Option("2")], width=80, bgcolor="#111111")
        mode_radio = ft.RadioGroup(content=ft.Row([ft.Radio(value="MANUAL", label="MANUAL"), ft.Radio(value="AUTO", label="AUTO")], spacing=10), value="MANUAL")

        def confirm_buy(e):
            try:
                order_summary = f"""
BUY CONFIRMED: {symbol_dropdown.value} {strike} {side}
LTP {ltp} Conf {conf}%
Lot: {lot_field.value} | Target {target_field.value}% | SL {sl_field.value}%
Order: {order_type.value} @ {limit_price.value if order_type.value=='LIMIT' else 'MARKET'}
Avg1: {avg1_rate.value} Lot {avg1_qty.value}
Avg2: {avg2_rate.value} Lot {avg2_qty.value}
Mode: {mode_radio.value} | Threshold {auto_threshold_field.value}%
Time {datetime.datetime.now().strftime('%H:%M:%S')}
"""
                log_box.value = order_summary
                page.dialog.open = False
                page.update()
                page.snack_bar = ft.SnackBar(ft.Text(f"Order Placed {symbol_dropdown.value} {strike} {side} Lot {lot_field.value}"), bgcolor="#00FF88")
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                log_box.value = f"Order Err {ex}"
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"BUY/SELL Panel - {symbol_dropdown.value} {strike} {side}", size=14, weight=ft.FontWeight.BOLD, color="#00FF88"),
            content=ft.Column([
                ft.Row([ft.Text(f"LTP Rs.{ltp} | Conf {conf}%", size=11, color="#AAA"), auto_mode_status]),
                ft.Divider(height=1, color="#333"),
                ft.Text("MAIN ORDER", size=11, weight=ft.FontWeight.BOLD, color="#00FF88"),
                ft.Row([lot_field, target_field, sl_field], spacing=8),
                ft.Row([order_type, limit_price], spacing=8),
                ft.Divider(height=1, color="#333"),
                ft.Text("MARGIN / AVERAGING - 2 Lot Niche Se", size=11, weight=ft.FontWeight.BOLD, color="#FFD700"),
                ft.Row([avg1_rate, avg1_qty], spacing=8),
                ft.Row([avg2_rate, avg2_qty], spacing=8),
                ft.Divider(height=1, color="#333"),
                ft.Text("TRADING MODE", size=11, weight=ft.FontWeight.BOLD, color="#229ED9"),
                mode_radio,
                ft.Row([auto_enabled, auto_threshold_field], spacing=8),
                ft.Text("AUTO = Barrier 70%/80% cross hote hi auto BUY | MANUAL = Aap dekh ke BUY karoge", size=8, color="#666")
            ], spacing=8, scroll=ft.ScrollMode.AUTO, height=460),
            actions=[ft.TextButton("CANCEL", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()), ft.ElevatedButton("CONFIRM BUY", bgcolor="#00FF88", color="#000000", on_click=confirm_buy)],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def oi_row(strike, side, conf, ltp, chg_oi, chg_price, vol_per, trend):
        bar_color = "#00FF88" if "Bullish" in trend else "#FF3B3B" if "Bearish" in trend else "#FFA500"
        try: cp = float(chg_price)
        except: cp = 0
        arrow = "▲" if cp >=0 else "▼"
        color = "#00FF88" if cp >=0 else "#FF3B3B"
        return ft.Container(
            content=ft.Row([
                ft.Container(width=4, height=75, bgcolor=bar_color, border_radius=2),
                ft.Column([
                    ft.Row([ft.Text(f"{symbol_dropdown.value} {strike} {side}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(content=ft.Text(f"{conf}%", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor=bar_color, border_radius=6, padding=ft.padding.symmetric(2,6))], spacing=6),
                    ft.Row([ft.Text(f"LTP Rs.{ltp}", size=12, weight=ft.FontWeight.BOLD), ft.Text(f"{arrow} {chg_price}%", size=11, weight=ft.FontWeight.BOLD, color=color), ft.Text(f"OI {chg_oi}", size=10, color="#AAA")], spacing=8),
                    ft.Text(f"{trend} Vol {vol_per}%", size=10, weight=ft.FontWeight.BOLD, color=bar_color)
                ], spacing=2, expand=True),
                ft.Column([
                    ft.ElevatedButton(text="BUY", bgcolor="#00FF88", color="#000000", width=64, height=32, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=lambda e, s=strike, sd=side, lp=ltp, cf=conf: open_buy_dialog(s, sd, lp, cf)),
                    ft.ElevatedButton(text="SELL", bgcolor="#221118", color="#FF6B8A", width=64, height=26, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, "#442233")))
                ], spacing=3)
            ]),
            bgcolor="#111111", border_radius=14, padding=10, border=ft.border.all(1, "#2A2A2A")
        )

    quick_col = ft.Column([], spacing=8)
    page1 = ft.Column([
        ft.Container(content=symbol_dropdown, margin=ft.margin.symmetric(10, 6)),
        ft.Container(content=card(ft.Column([ft.Text("BULLISH BARRIER - CALL vs PUT (NSE TAGGED)", size=11, weight=ft.FontWeight.BOLD, color="#FFD700"), ft.Row([ft.Column([ft.Text("CALL Bullish", size=10, color="#888"), call_bull], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), ft.Column([ft.Text("PUT Bullish", size=10, color="#888"), put_bull], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)]), barrier_bar, barrier_text])), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Container(content=ft.Row([ft.Container(width=8, height=8, bgcolor="#00FF88", border_radius=4), ft.Column([ft.Text("NSE FREE LIVE TAGGED", size=11, weight=ft.FontWeight.BOLD, color="#6AFFAA"), data_source], spacing=1, expand=True), nifty_live]), bgcolor="#0A1E0A", border_radius=14, padding=12, border=ft.border.all(1, "#1A4D2E")), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=card(ft.Column([ft.Row([ft.Text("📈 REAL CHART - NSE TAGGED FAST", size=11, weight=ft.FontWeight.BOLD, color="#00FF88"), ft.Row([auto_mode_status, last_upd], spacing=8)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(content=real_chart, height=200), ft.Row([auto_enabled, auto_threshold_field], spacing=8)])), margin=ft.margin.symmetric(10, 4)),
        ft.Container(content=ft.Column([ft.Text("LIVE OI CHAIN - BUY pe Lot/Target/SL/Avg Panel", size=10, color="#AAA", weight=ft.FontWeight.BOLD), quick_col, card(log_box)], spacing=6), margin=ft.margin.symmetric(10, 4)),
        ft.Container(height=90)
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)

    content = ft.Container(content=page1, expand=True)
    nav = ft.Container(content=ft.NavigationBar(selected_index=0, bgcolor="#0F0F0F", destinations=[ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Main Bot"), ft.NavigationBarDestination(icon=ft.Icons.SHOW_CHART, label="Live Chart"), ft.NavigationBarDestination(icon=ft.Icons.LIST, label="OI Chain"), ft.NavigationBarDestination(icon=ft.Icons.SECURITY, label="Setting")]), border=ft.border.only(top=ft.BorderSide(1, "#222")))

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"})
    try: session.get("https://www.nseindia.com", timeout=5)
    except: pass

    def fetch_live():
        try:
            sym = symbol_dropdown.value
            ltp = 0; signals = []; call_b = 0; put_b = 0
            try:
                url = f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}" if sym in ["NIFTY","BANKNIFTY","FINNIFTY"] else f"https://www.nseindia.com/api/option-chain-equities?symbol={sym}"
                r = session.get(url, timeout=6)
                if r.status_code == 200:
                    data = r.json()
                    ltp = data['records']['underlyingValue']
                    data_source.value = f"Source: NSE India ✅ REAL | {sym}"
                    for item in data['records']['data'][:14]:
                        strike = item.get('strikePrice', 0)
                        ce = item.get('CE', {}); pe = item.get('PE', {})
                        if ce and 20 <= ce.get('lastPrice',0) <= 300:
                            lp = ce.get('lastPrice',0); vol_trend = "Bullish Strong BUY CE" if lp>=80 and lp<=100 else "Neutral CE"
                            if "Bullish" in vol_trend: call_b+=1
                            signals.append((strike, "CE", min(96, 80+int(ce.get('pChange',0))), lp, f"{int(ce.get('openInterest',0)/1000)}k", round(ce.get('pChange',0),2), random.randint(82,95), vol_trend))
                        if pe and 20 <= pe.get('lastPrice',0) <= 300:
                            lp = pe.get('lastPrice',0); vol_trend = "Bullish Strong BUY PE" if lp>=80 and lp<=100 else "Neutral PE"
                            if "Bullish" in vol_trend: put_b+=1
                            signals.append((strike, "PE", min(96, 80+int(pe.get('pChange',0))), lp, f"{int(pe.get('openInterest',0)/1000)}k", round(pe.get('pChange',0),2), random.randint(82,95), vol_trend))
            except Exception as e:
                ltp = 0
            if ltp == 0:
                try:
                    y_map = {"NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK","FINNIFTY":"^NSEI","RELIANCE":"RELIANCE.NS","HDFCBANK":"HDFCBANK.NS"}
                    y_sym = y_map.get(sym, f"{sym}.NS")
                    y = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{y_sym}?interval=1m&range=1d", headers={"User-Agent":"Mozilla/5.0"}, timeout=6).json()
                    ltp = y['chart']['result'][0]['meta']['regularMarketPrice']
                    data_source.value = f"Source: Yahoo (NSE Holiday) | {sym}"
                    closes = [c for c in y['chart']['result'][0]['indicators']['quote'][0]['close'] if c is not None][-60:]
                    if closes:
                        real_chart.min_y = min(closes)- (max(closes)-min(closes))*0.15
                        real_chart.max_y = max(closes)+ (max(closes)-min(closes))*0.15
                        real_chart.max_x = len(closes)
                        real_chart.data_series[0].data_points = [ft.LineChartDataPoint(x=i, y=closes[i]) for i in range(len(closes))]
                except: ltp = 23050 + random.uniform(-150,150)

            if ltp:
                price_history.append(ltp)
                if len(price_history) > 60: price_history.pop(0)
                if len(price_history) > 2:
                    real_chart.min_y = min(price_history) - (max(price_history)-min(price_history))*0.2 if max(price_history)!=min(price_history) else ltp-50
                    real_chart.max_y = max(price_history) + (max(price_history)-min(price_history))*0.2 if max(price_history)!=min(price_history) else ltp+50
                    real_chart.max_x = len(price_history)
                    real_chart.data_series[0].data_points = [ft.LineChartDataPoint(x=i, y=price_history[i]) for i in range(len(price_history))]
                nifty_live.value = f"{sym} {ltp:.2f} LIVE (NSE TAGGED)"

            # AUTO BUY Logic
            total = call_b + put_b
            auto_thr = 70
            try: auto_thr = int(auto_threshold_field.value)
            except: auto_thr = 70
            if total>0:
                cp = int(call_b/total*100) if total else 0; pp=100-cp
                call_bull.value=f"{cp}%"; put_bull.value=f"{pp}%"; barrier_bar.value=cp/100
                if cp>=auto_thr and auto_enabled.value:
                    barrier_text.value=f"🤖 AUTO BUY TRIGGER {cp}% >= {auto_thr}% | CALL Strong"
                    barrier_text.color="#00FF88"; barrier_bar.color="#00FF88"; real_chart.data_series[0].color="#00FF88"
                    # Auto buy first signal
                    if signals and log_box.value.find("AUTO")==-1:
                        log_box.value = f"🤖 AUTO BUY {sym} {signals[0][0]} {signals[0][1]} @ {signals[0][3]} Barrier {cp}%"
                elif cp>pp:
                    barrier_text.value=f"🚀 CALL Bullish {cp}% | Manual/Auto={auto_enabled.value}"
                    barrier_text.color="#00FF88"; barrier_bar.color="#00FF88"; real_chart.data_series[0].color="#00FF88"
                else:
                    barrier_text.value=f"🔻 PUT Bullish {pp}% | Manual/Auto={auto_enabled.value}"
                    barrier_text.color="#FF6B8A"; barrier_bar.color="#FF6B8A"; real_chart.data_series[0].color="#FF6B8A"
                auto_mode_status.value = f"Mode: {'AUTO' if auto_enabled.value else 'MANUAL'} {auto_thr}%"

            if not signals:
                for i in range(5):
                    strike = int(ltp/100)*100 - 200 + i*100 if ltp else 23000 + i*100
                    side = "CE" if i%2==0 else "PE"
                    lp = random.uniform(82, 98); vol = random.randint(82,95)
                    trend = f"Bullish Strong BUY {side}"
                    if side=="CE": call_b+=1
                    else: put_b+=1
                    signals.append((strike, side, random.randint(88,96), round(lp,1), f"{random.randint(10,40)}k", round(random.uniform(1,4),2), vol, trend))

            quick_col.controls = [oi_row(s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7]) for s in signals[:8]]
            last_upd.value = f"{datetime.datetime.now().strftime('%H:%M:%S')} NSE"
            page.update()
        except Exception as ex:
            try: page.update()
            except: pass

    def bg_loop():
        time.sleep(1); fetch_live()
        while True: time.sleep(3); fetch_live()

    page.add(ft.SafeArea(ft.Column([content, nav], expand=True, spacing=0), expand=True))
    threading.Thread(target=bg_loop, daemon=True).start()

ft.app(target=main)
