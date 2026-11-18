"""BOT KING V2 presentation-only copy of audited V1 dark/gold visual tokens.

No V1 preferences, server API, credentials, provider choice or order actions.
Only imported by the V2 Flet app. Colors and layout values match V1 main.
"""
BG = "#080F18"
PANEL = "#102735"
PANEL2 = "#12313E"
GOLD = "#E9B949"
GREEN = "#16C784"
RED = "#FF7890"
WHITE = "#EAF1F6"
MUTED = "#A9BBC5"
BORDER = "#718796"
NAV_BG = "#102330"
BODY_SIZE = 14
HEADING_SIZE = 17
INDEX_TITLE_SIZE = 16
HEADER_SIZE = 18
CARD_PADDING = 7
CARD_RADIUS = 10


def apply_v1_theme(page, ft):
    """Safe UI-only theme: never change Android identity or business state."""
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=GOLD, on_primary=BG,
            secondary=GOLD, on_secondary=BG,
            surface=PANEL, on_surface=WHITE,
            error=RED, on_error=BG, outline=BORDER))


def v1_text(ft, value, *, size=BODY_SIZE, color=WHITE, bold=False):
    return ft.Text(str(value), size=max(BODY_SIZE, size), color=color,
                   weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL)


def v1_card(ft, children, *, expand=False):
    return ft.Container(
        content=ft.Column(list(children), spacing=4,
                          horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        bgcolor=PANEL, border_radius=CARD_RADIUS, padding=CARD_PADDING,
        border=ft.border.all(1, BORDER), expand=expand)


def v1_header(ft, version):
    """Matches V1 trophy / title / visible version / bell chrome."""
    return ft.Container(content=ft.Row([
        ft.Icon(ft.Icons.EMOJI_EVENTS, color=GOLD, size=24),
        ft.Row([v1_text(ft, "BOT KING", size=HEADER_SIZE, color=GOLD, bold=True),
                v1_text(ft, "v" + str(version), color=MUTED)], spacing=8, wrap=True),
        ft.Container(expand=True),
        ft.Icon(ft.Icons.NOTIFICATIONS_NONE, color=GOLD, size=24),
    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.only(left=12, right=12, top=8, bottom=5), bgcolor=BG)
