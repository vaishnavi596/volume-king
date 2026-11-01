    def oi_row(strike, side, conf, ltp, chg_oi, chg_price, vol_per, trend="Bullish"):
        # Trend color + arrow
        is_bull = "Bullish" in trend
        is_over = "Overbought" in trend
        bar_color = "#00FF88" if is_bull else "#FF3B3B" if not is_over else "#FF6B35"
        arrow = "▲" if float(chg_price) >=0 else "▼"
        price_color = "#00FF88" if float(chg_price) >=0 else "#FF3B3B"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(width=4, height=68, bgcolor=bar_color, border_radius=2),
                    ft.Column([
                        ft.Row([
                            ft.Text(f"{symbol_dropdown.value} {strike} {side}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Container(
                                content=ft.Text(f"{conf}%", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                                bgcolor=bar_color, border_radius=6, padding=ft.padding.symmetric(2,6)
                            ),
                        ], spacing=6),
                        ft.Row([
                            ft.Text(f"LTP: ₹{ltp}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(f"{arrow} {chg_price}%", size=11, weight=ft.FontWeight.BOLD, color=price_color),
                            ft.Text(f"OI: {chg_oi}", size=10, color="#AAA"),
                        ], spacing=8),
                        ft.Row([
                            ft.Text(trend, size=10, weight=ft.FontWeight.BOLD, color=bar_color),
                            ft.Text(f"• Vol {vol_per}%", size=9, color="#888"),
                            ft.Text(f"• Range 80-100", size=9, color="#666"),
                        ], spacing=6),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Container(content=ft.Text("BUY", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor="#00FF88", border_radius=8, padding=ft.padding.symmetric(6,12), width=58, height=30, alignment=ft.alignment.center),
                        ft.Container(content=ft.Text("SELL", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_300), bgcolor="#221118", border_radius=8, padding=ft.padding.symmetric(4,10), width=58, height=26, border=ft.border.all(1,"#442233"), alignment=ft.alignment.center),
                    ], spacing=4)
                ]),
            ]),
            bgcolor="#111111", border_radius=14, padding=ft.padding.only(left=0, right=10, top=8, bottom=8), 
            border=ft.border.all(1,"#2A2A2A"), margin=ft.margin.only(bottom=2)
        )
