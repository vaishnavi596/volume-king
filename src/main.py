
import flet as ft
import asyncio
import json
import urllib.request
from datetime import datetime

def get_nifty_data():
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        "%5ENSEI?range=1d&interval=5m"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode())

    result = data["chart"]["result"][0]
    meta = result["meta"]
    quote = result["indicators"]["quote"][0]

    price = meta.get("regularMarketPrice")
    previous = meta.get("previousClose")

    if price is None:
        raise ValueError("NIFTY price unavailable")

    volumes = quote.get("volume") or []
    closes = quote.get("close") or []

    total_volume = 0
    total_value = 0

    for close, volume in zip(closes, volumes):
        if close is not None and volume:
            total_value += close * volume
            total_volume += volume

    vwap = total_value / total_volume if total_volume else None

    change = price - previous if previous else None
    change_pct = (change / previous * 100) if previous else None

    return {
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "vwap": vwap,
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }


def main(page: ft.Page):
    page.title = "VOLUME KING 97 V8"
    page.bgcolor = "#080D18"
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    mode = "LIVE"
    current_data = None

    status = ft.Text("डेटा अभी लोड नहीं हुआ", color="#FFC857")
    price_text = ft.Text("--", size=34, weight="bold", color="white")
    change_text = ft.Text("--", size=17, color="white")
    vwap_text = ft.Text("--", size=19, color="#55D6BE")
    time_text = ft.Text("--", size=12, color="#AAB4C5")
    mode_text = ft.Text("LIVE MODE", color="#55D6BE", size=16)
    trade_text = ft.Text(
        "CE / PE सिमुलेशन के लिए बटन दबाएँ",
        color="white",
        size=14
    )

    def panel(title, content):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, color="#AAB4C5", size=13),
                content
            ], spacing=8),
            bgcolor="#172235",
            padding=16,
            border_radius=12,
            expand=True
        )

    async def refresh_data(e=None):
        status.value = "NIFTY डेटा लोड हो रहा है..."
        page.update()

        try:
            data = await asyncio.to_thread(get_nifty_data)
            current_data = data

            price_text.value = f"{data['price']:,.2f}"

            if data["change"] is not None:
                change_text.value = (
                    f"बदलाव: {data['change']:+.2f} "
                    f"({data['change_pct']:+.2f}%)"
                )
                change_text.color = (
                    "#55D6BE" if data["change"] >= 0 else "#FF7272"
                )
            else:
                change_text.value = "बदलाव उपलब्ध नहीं"

            vwap_text.value = (
                f"{data['vwap']:,.2f} (अनुमानित)"
                if data["vwap"] is not None
                else "उपलब्ध नहीं"
            )

            time_text.value = (
                f"प्राप्ति समय: {data['time']}"
            )
            status.value = (
                "डेटा स्रोत: Yahoo Finance Chart API | "
                "डेटा विलंबित हो सकता है"
            )

        except Exception as error:
            status.value = (
                "डेटा नहीं मिला। इंटरनेट या डेटा स्रोत जाँचें।"
            )
            price_text.value = "--"
            change_text.value = "--"
            vwap_text.value = "--"
            time_text.value = str(error)[:100]

        page.update()

    def set_demo(e):
        nonlocal mode
        mode = "DEMO"
        mode_text.value = "DEMO MODE"
        mode_text.color = "#FFC857"
        trade_text.value = "DEMO मोड: केवल सिमुलेशन"
        page.update()

    def set_live(e):
        nonlocal mode
        mode = "LIVE"
        mode_text.value = "LIVE MODE"
        mode_text.color = "#55D6BE"
        trade_text.value = "LIVE डेटा मोड: असली ट्रेडिंग चालू नहीं है"
        page.update()

    def simulate_trade(side):
        trade_text.value = (
            f"{side} सिमुलेशन चुना गया। "
            "कोई असली ऑर्डर नहीं भेजा गया।"
        )
        page.update()

    page.add(
        ft.Column([
            ft.Text(
                "VOLUME KING 97",
                size=27,
                weight="bold",
                color="#55D6BE"
            ),
            ft.Text("V8 MARKET DASHBOARD", color="white", size=15),
            ft.Divider(color="#34445C"),

            mode_text,
            ft.Row([
                ft.ElevatedButton("LIVE MODE", on_click=set_live),
                ft.ElevatedButton("DEMO MODE", on_click=set_demo)
            ]),

            panel("NIFTY 50", price_text),
            change_text,
            panel("VWAP", vwap_text),

            ft.Text(
                "OPTIONS DATA",
                size=17,
                color="#55D6BE",
                weight="bold"
            ),
            ft.Text("PCR: उपलब्ध नहीं - Options Chain डेटा आवश्यक",
                    color="white"),
            ft.Text("CALL VOLUME: उपलब्ध नहीं", color="white"),
            ft.Text("PUT VOLUME: उपलब्ध नहीं", color="white"),

            ft.Divider(color="#34445C"),
            ft.Text("SIMULATION TRADING", color="#55D6BE", size=17),

            ft.Row([
                ft.ElevatedButton(
                    "BUY CE (SIMULATION)",
                    bgcolor="#087F5B",
                    color="white",
                    on_click=lambda e: simulate_trade("BUY CE")
                ),
                ft.ElevatedButton(
                    "BUY PE (SIMULATION)",
                    bgcolor="#B02A37",
                    color="white",
                    on_click=lambda e: simulate_trade("BUY PE")
                )
            ]),
            trade_text,

            ft.ElevatedButton(
                "REFRESH NIFTY DATA",
                on_click=refresh_data
            ),
            status,
            time_text,

            ft.Text(
                "शिक्षण और सिमुलेशन के लिए। "
                "यह ऐप ब्रोकर ऑर्डर नहीं भेजता।",
                color="#AAB4C5",
                size=11
            )
        ], spacing=14)
    )

    page.run_task(refresh_data)


ft.app(target=main)
