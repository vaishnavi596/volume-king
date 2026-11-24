"""NSE/BSE equity regular-session holiday gate for BOT KING V3 (offline).

2026 schedule transcribed from NSE Capital Market circular NSE/CMTR/71775
(12 Dec 2025) including 15-Jan-2026 subsequently published holiday.
This static calendar is NOT an exchange-live status service. Unscheduled
closures and special Muhurat timings must be separately authenticated.
No network, broker calls or orders.
"""
from datetime import datetime, timedelta, timezone

IST=timezone(timedelta(hours=5,minutes=30))
EQUITY_HOLIDAYS_2026=frozenset((
    "2026-01-15", "2026-01-26", "2026-03-03",
    "2026-03-26", "2026-03-31", "2026-04-03",
    "2026-04-14", "2026-05-01", "2026-05-28",
    "2026-06-26", "2026-09-14", "2026-10-02",
    "2026-10-20", "2026-11-10", "2026-11-24",
    "2026-12-25",
))
# 08-Nov-2026 Muhurat is a separate special weekend session; regular
# hours do not infer its session window or classify it as ordinary LIVE.

def ist_clock(now=None):
    if now is None:
        return datetime.now(IST)
    if not isinstance(now,datetime):
        raise TypeError("datetime required for exchange session check")
    if now.tzinfo is None or now.utcoffset() is None:
        # Avoid silently treating a device-local wall-clock as IST.
        raise ValueError("Exchange session datetime must be timezone aware")
    return now.astimezone(IST)

def regular_equity_day(now=None):
    clock=ist_clock(now)
    if clock.weekday()>=5:
        return False
    # 2027+ cannot claim regular LIVE eligibility from weekday-only dates
    # until a separately verified, versioned NSE/BSE calendar is installed.
    # Fail closed: cached HIST analysis remains available, automatic polling
    # and LIVE eligibility are disabled for an unverified future year.
    if clock.year>=2027:
        return False
    if clock.year==2026 and clock.date().isoformat() in EQUITY_HOLIDAYS_2026:
        return False
    return True

def equity_session_closed_detail(now=None):
    """User-facing OFF reason, never a claim that live quotes are verified.

    Muhurat is a special session requiring separate source/timeframe proof;
    its date alone cannot activate an ordinary NSE/BSE equity LIVE vote.
    """
    clock=ist_clock(now)
    if clock.year>=2027:
        return " • official holiday calendar unavailable"
    if clock.year==2026 and clock.date().isoformat()=="2026-11-08":
        return " • special Muhurat session not enabled"
    if clock.year==2026 and clock.date().isoformat() in EQUITY_HOLIDAYS_2026:
        return " • NSE/BSE trading holiday"
    if clock.weekday()>=5:
        return " • weekend"
    return " • outside regular market hours"

def regular_equity_hours(now=None):
    clock=ist_clock(now)
    return regular_equity_day(clock) and (9,15)<=(clock.hour,clock.minute)<(15,30)

def equity_refresh_window(now=None):
    clock=ist_clock(now)
    return regular_equity_day(clock) and (9,10)<=(clock.hour,clock.minute)<(15,45)
