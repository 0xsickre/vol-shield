"""FOMC meeting window overlay for shield payload."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

FOMC_RISK_ON_SHRINK = 0.50

FOMC_MEETINGS: dict[int, list[tuple[date, date]]] = {
    2026: [
        (date(2026, 1, 27), date(2026, 1, 28)),
        (date(2026, 3, 17), date(2026, 3, 18)),
        (date(2026, 4, 28), date(2026, 4, 29)),
        (date(2026, 6, 16), date(2026, 6, 17)),
        (date(2026, 7, 28), date(2026, 7, 29)),
        (date(2026, 9, 15), date(2026, 9, 16)),
        (date(2026, 10, 27), date(2026, 10, 28)),
        (date(2026, 12, 8), date(2026, 12, 9)),
    ],
    2027: [
        (date(2027, 1, 26), date(2027, 1, 27)),
        (date(2027, 3, 16), date(2027, 3, 17)),
        (date(2027, 4, 27), date(2027, 4, 28)),
        (date(2027, 6, 8), date(2027, 6, 9)),
        (date(2027, 7, 27), date(2027, 7, 28)),
        (date(2027, 9, 14), date(2027, 9, 15)),
        (date(2027, 10, 26), date(2027, 10, 27)),
        (date(2027, 12, 7), date(2027, 12, 8)),
    ],
}


def coerce_asof_date(asof: Any) -> date | None:
    if asof is None:
        return None
    if isinstance(asof, datetime):
        return asof.date()
    if isinstance(asof, date):
        return asof
    if hasattr(asof, "date"):
        try:
            d = asof.date()
            if isinstance(d, date):
                return d
        except (TypeError, ValueError, AttributeError):
            pass
    if isinstance(asof, str):
        try:
            return date.fromisoformat(str(asof).strip()[:10])
        except ValueError:
            return None
    return None


def fomc_meeting_window(asof: Any) -> dict[str, Any]:
    d = coerce_asof_date(asof)
    if d is None:
        d = date.today()
    meetings = FOMC_MEETINGS.get(d.year)
    if not meetings:
        return {"active": False, "meeting_start": None, "meeting_end": None, "shrink": 1.0}
    for start, end in meetings:
        window_start = start - timedelta(days=1)
        if window_start <= d <= end:
            return {
                "active": True,
                "meeting_start": start.isoformat(),
                "meeting_end": end.isoformat(),
                "shrink": FOMC_RISK_ON_SHRINK,
            }
    return {"active": False, "meeting_start": None, "meeting_end": None, "shrink": 1.0}


def fomc_shield_fields(asof: Any = None) -> dict[str, Any]:
    return fomc_meeting_window(asof)
