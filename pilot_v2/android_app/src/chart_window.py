"""Pure local display window selector; no provider requests."""
WINDOWS = (15, 35, 70)
DEFAULT_WINDOW = 35

def choose_chart_window(value):
    if type(value) is not int or value not in WINDOWS:
        raise ValueError("Unsupported historical chart window")
    return value

def window_from_dropdown(value):
    if type(value) is not str or value not in tuple(str(n) for n in WINDOWS):
        raise ValueError("Unsupported chart window choice")
    return choose_chart_window(int(value))
