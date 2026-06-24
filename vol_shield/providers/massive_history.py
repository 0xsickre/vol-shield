"""Massive daily aggregates to close price series."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import pandas as pd

from vol_shield.core.reference_data import massive_symbol_for
from vol_shield.platform.secrets import get_secret
from vol_shield.providers.massive_rate_limiter import acquire_massive_slot
from vol_shield.providers.retry_http import requests_get_retry

_MASSIVE_AGGS_URL = "https://api.massive.com/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"

_PERIOD_DAYS: dict[str, int] = {
    "60d": 90,
    "90d": 120,
    "400d": 450,
}


def _parse_period_days(period: str | None) -> int:
    if not period:
        return 400
    p = str(period).strip().lower()
    if p in _PERIOD_DAYS:
        return _PERIOD_DAYS[p]
    m = re.match(r"^(\d+)(d|mo|y)$", p)
    if not m:
        return 400
    n = int(m.group(1))
    unit = m.group(2)
    if unit == "d":
        return max(n + 5, 10)
    if unit == "mo":
        return n * 31 + 10
    return n * 366 + 10


def _date_range(*, start: Any = None, end: Any = None, period: str | None = None) -> tuple[str, str]:
    end_dt = pd.Timestamp(end).date() if end is not None else date.today()
    if start is not None:
        start_dt = pd.Timestamp(start).date()
    else:
        start_dt = end_dt - timedelta(days=_parse_period_days(period))
    if start_dt > end_dt:
        start_dt = end_dt - timedelta(days=30)
    return start_dt.isoformat(), end_dt.isoformat()


def massive_history_close_series(
    yahoo_ticker: str,
    *,
    start: Any = None,
    end: Any = None,
    period: str | None = None,
    interval: str = "1d",
    auto_adjust: bool = True,
) -> pd.Series:
    _ = interval, auto_adjust
    sym = str(yahoo_ticker or "").strip()
    massive_sym = massive_symbol_for(sym)
    if not massive_sym:
        return pd.Series(dtype=float)

    api_key = (get_secret("MASSIVE_API_KEY", "") or "").strip()
    if not api_key:
        return pd.Series(dtype=float)

    start_s, end_s = _date_range(start=start, end=end, period=period)
    url = _MASSIVE_AGGS_URL.format(
        ticker=quote(massive_sym, safe=""),
        start=start_s,
        end=end_s,
    )
    params = {"adjusted": "true", "sort": "asc", "limit": 50000}
    headers = {"Authorization": f"Bearer {api_key}"}

    acquire_massive_slot()
    res = requests_get_retry(
        url,
        params=params,
        headers=headers,
        timeout=20,
        attempts=3,
        base_seconds=1.5,
        default=None,
    )
    if res is None:
        return pd.Series(dtype=float)

    try:
        payload = res.json()
    except Exception:
        return pd.Series(dtype=float)

    results = payload.get("results") if isinstance(payload, dict) else None
    if not results:
        return pd.Series(dtype=float)

    rows: list[tuple[datetime, float]] = []
    for bar in results:
        if not isinstance(bar, dict):
            continue
        ts = bar.get("t")
        close = bar.get("c")
        if ts is None or close is None:
            continue
        try:
            dt = datetime.fromtimestamp(int(ts) / 1000.0, tz=timezone.utc).replace(tzinfo=None)
            val = float(close)
        except (TypeError, ValueError, OSError):
            continue
        rows.append((dt, val))

    if not rows:
        return pd.Series(dtype=float)

    rows.sort(key=lambda x: x[0])
    idx = pd.DatetimeIndex([r[0] for r in rows])
    return pd.Series([r[1] for r in rows], index=idx, dtype=float).sort_index()
