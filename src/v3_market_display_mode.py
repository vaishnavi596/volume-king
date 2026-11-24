"""Evidence-driven two-state data display.

Only LIVE and HISTORICAL are data modes. WAIT is the lack of any validated
display evidence, never a third mode. Manual legacy modes are migrated away.
Holiday calendars may pace provider calls, but do not choose the display mode.
"""
MODES=("LIVE","HISTORICAL")

def normalized_mode(value):
    """Migrate old phone preferences to automatic source selection."""
    return "AUTO"

def resolve_mode(value=None, *, session_eligible=None, live_verified=False,
                 history_valid=False):
    """Select source by evidence only, not weekday, calendar or manual setting.

    Callers MUST independently validate broker, exact timeframe, source and
    exchange timestamp before setting live_verified=True.
    """
    if live_verified is True:
        return "LIVE"
    if history_valid is True:
        return "HIST"
    return "WAIT"
