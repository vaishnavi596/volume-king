from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

# COLORS - V7 DARK LUXURY
BG = [0.04, 0.06, 0.09, 1]
CARD = [0.09, 0.12, 0.18, 1]
CARD2 = [0.14, 0.18, 0.25, 1]
GOLD = [1, 0.84, 0, 1]
GREEN = [0.15, 0.8, 0.4, 1]
RED = [1, 0.3, 0.3, 1]
BLUE = [0.2, 0.5, 1, 1]
WHITE = [1, 1, 1, 1]
GRAY = [0.6, 0.65, 0.7, 1]

class RoundedCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(12)
        with self.canvas.before:
            Color(*CARD)
            self.rect = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self.update_rect, size=self.update_rect)
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class MainDashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        # Top Chips
        chip_box = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        for name in ["NIFTY", "BANKNIFTY", "FINNIFTY", "+ ADD"]:
            b = Button(text=name, size_hint_x=None, width=dp(85), background_color=CARD2, background_normal='', color=GOLD if name=="NIFTY" else WHITE, font_size=dp(10), bold=True)
            chip_box.add_widget(b)
        root.add_widget(chip_box)
        
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # FINAL 68% CARD
        final_card = RoundedCard(orientation='vertical', size_hint_y=None, height=dp(170))
        final_card.add_widget(Label(text="FINAL MARKET SENTIMENT - 100% COMBINED", color=GOLD, font_size=dp(10), bold=True, size_hint_y=None, height=dp(18)))
        mid = BoxLayout(spacing=dp(10))
        left = BoxLayout(orientation='vertical')
        left.add_widget(Label(text="68%", color=GREEN, font_size=dp(32), bold=True))
        left.add_widget(Label(text="BULLISH", color=GREEN, font_size=dp(13), bold=True))
        left.add_widget(Label(text="40+40+20", color=GRAY, font_size=dp(8)))
        mid.add_widget(left)
        right = BoxLayout(orientation='vertical', spacing=dp(3))
        right.add_widget(Label(text="Premium 40%: 68% Bull", color=WHITE, font_size=dp(10)))
        right.add_widget(Label(text="Nifty 40%: 62% Bull", color=WHITE, font_size=dp(10)))
        right.add_widget(Label(text="News 20%: 75% Positive", color=WHITE, font_size=dp(10)))
        right.add_widget(Label(text="Calculation: OI x LTP", color=GRAY, font_size=dp(8)))
        mid.add_widget(right)
        final_card.add_widget(mid)
        content.add_widget(final_card)

        # PREMIUM BASE 40%
        c1 = RoundedCard(orientation='vertical', size_hint_y=None, height=dp(120))
        c1.add_widget(Label(text="PREMIUM BASE 40% - Paisa Kaha Laga?", color=GOLD, font_size=dp(11), bold=True, size_hint_y=None, height=dp(20)))
        row = BoxLayout(spacing=dp(8))
        row.add_widget(Label(text="CALL\nRs 12.5 Cr\n68% Bullish", color=GREEN, font_size=dp(11)))
        row.add_widget(Label(text="PUT\nRs 5.8 Cr\n32% Bearish", color=RED, font_size=dp(11)))
        c1.add_widget(row)
        content.add_widget(c1)

        # NIFTY BASE 40%
        c2 = RoundedCard(orientation='vertical', size_hint_y=None, height=dp(100))
        c2.add_widget(Label(text="NIFTY BASE 40% - Barrier", color=GOLD, font_size=dp(11), bold=True, size_hint_y=None, height=dp(20)))
        row2 = BoxLayout()
        row2.add_widget(Label(text="CALL Barrier: 62%", color=GREEN, font_size=dp(11)))
        row2.add_widget(Label(text="PUT Barrier: 38%", color=RED, font_size=dp(11)))
        c2.add_widget(row2)
        content.add_widget(c2)

        # NEWS BASE 20%
        c3 = RoundedCard(orientation='vertical', size_hint_y=None, height=dp(100))
        c3.add_widget(Label(text="NEWS BASE 20%", color=GOLD, font_size=dp(11), bold=True, size_hint_y=None, height=dp(20)))
        row3 = BoxLayout()
        row3.add_widget(Label(text="Positive: 75%", color=BLUE, font_size=dp(11)))
        row3.add_widget(Label(text="Negative: 25%", color=RED, font_size=dp(11)))
        c3.add_widget(row3)
        c3.add_widget(Label(text="Source: CNBC, MoneyControl", color=GRAY, font_size=dp(8), size_hint_y=None, height=dp(15)))
        content.add_widget(c3)

        # NSE LIVE
        c4 = RoundedCard(size_hint_y=None, height=dp(45))
        c4.add_widget(Label(text="NSE LIVE: NIFTY 24123.45 +0.85% | BANKNIFTY 51200", color=GREEN, font_size=dp(10), bold=True))
        content.add_widget(c4)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

class ChartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        b = BoxLayout(orientation='vertical', padding=dp(12))
        b.add_widget(Label(text="LIVE CHART - EMA 9/21 | RSI | VWAP", color=GOLD, bold=True, size_hint_y=None, height=dp(40)))
        b.add_widget(Label(text="Chart Area - TradingView Style\nGreen Candles + Gold EMA Lines", color=GRAY))
        self.add_widget(b)

class OIChainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(10))
        root.add_widget(Label(text="LIVE OI CHAIN", color=GOLD, bold=True, size_hint_y=None, height=dp(30)))
        sv = ScrollView()
        lst = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        lst.bind(minimum_height=lst.setter('height'))
        for strike in [23900, 24000, 24100, 24200]:
            card = RoundedCard(orientation='horizontal', size_hint_y=None, height=dp(55))
            card.add_widget(Label(text=f"NIFTY {strike} CE\nOI Chg +15% Vol 95%", color=WHITE, font_size=dp(9)))
            card.add_widget(Button(text="BUY", size_hint_x=None, width=dp(55), background_color=GOLD, background_normal='', color=[0,0,0,1], font_size=dp(9)))
            lst.add_widget(card)
        sv.add_widget(lst)
        root.add_widget(sv)
        self.add_widget(root)

class BotScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="AUTO BOT STRATEGY", color=GOLD, bold=True, size_hint_y=None, height=dp(30)))
        sv = ScrollView()
        box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        for f in ["AUTO BUY ON", "OI Change >15% ON", "PCR 0.7-1.4 ON", "Supertrend ON", "Volume 80-100% ON", "Target 10% SL 5%"]:
            c = RoundedCard(orientation='horizontal', size_hint_y=None, height=dp(45))
            c.add_widget(Label(text=f, color=WHITE, font_size=dp(11)))
            c.add_widget(Switch(active=True))
            box.add_widget(c)
        box.add_widget(Button(text="SAVE STRATEGY", size_hint_y=None, height=dp(50), background_color=GOLD, background_normal='', color=[0,0,0,1], bold=True))
        sv.add_widget(box)
        root.add_widget(sv)
        self.add_widget(root)

class SettingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="API MANAGER & SETTING", color=GOLD, bold=True, size_hint_y=None, height=dp(30)))
        sv = ScrollView()
        box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        box.add_widget(Spinner(text="Angel One", values=["Angel One","Dhan","Zerodha","Upstox"], size_hint_y=None, height=dp(40), background_color=CARD2))
        for field in ["Client ID","Password","TOTP Secret","API Key","API Secret","MPIN"]:
            c = RoundedCard(orientation='vertical', size_hint_y=None, height=dp(60))
            c.add_widget(Label(text=field, color=GRAY, font_size=dp(8), size_hint_y=None, height=dp(12)))
            c.add_widget(TextInput(hint_text=field, size_hint_y=None, height=dp(35), background_color=CARD2, foreground_color=WHITE))
            box.add_widget(c)
        box.add_widget(Button(text="SAVE API & CONNECT", size_hint_y=None, height=dp(50), background_color=GOLD, background_normal='', color=[0,0,0,1], bold=True))
        box.add_widget(Label(text="BLUECHIP LIST: RELIANCE, TCS, HDFC", color=GRAY, font_size=dp(9), size_hint_y=None, height=dp(20)))
        sv.add_widget(box)
        root.add_widget(sv)
        self.add_widget(root)

class VolumeKingApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainDashboardScreen(name='main'))
        sm.add_widget(ChartScreen(name='chart'))
        sm.add_widget(OIChainScreen(name='oi'))
        sm.add_widget(BotScreen(name='bot'))
        sm.add_widget(SettingScreen(name='setting'))
        main = BoxLayout(orientation='vertical')
        main.add_widget(sm)
        nav = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(2), padding=dp(3))
        for label, screen in [("HOME","main"),("CHART","chart"),("OI CHAIN","oi"),("AUTO BOT","bot"),("SETTING","setting")]:
            btn = Button(text=label, font_size=dp(8), background_color=CARD2, background_normal='', color=GRAY)
            btn.bind(on_press=lambda x, s=screen: setattr(sm, 'current', s))
            nav.add_widget(btn)
        main.add_widget(nav)
        return main

if __name__ == '__main__':
    VolumeKingApp().run()
