"""Business-day gap and bar staleness primitives (shared, no domain I/O)."""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def series_last_ts(series: pd.Series | None) -> pd.Timestamp | None:
    if series is None or series.empty:
        return None
    try:
        return pd.Timestamp(series.index.max())
    except Exception:
        return None


def staleness_hours(ts: pd.Timestamp | None, ref: datetime) -> float | None:
    if ts is None or pd.isna(ts):
        return None
    t = pd.Timestamp(ts)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    ref_naive = ref.replace(tzinfo=None) if ref.tzinfo else ref
    try:
        return float((ref_naive - t.to_pydatetime()).total_seconds() / 3600.0)
    except Exception:
        return None


def business_day_gap(bar_date: object, ref_date: object) -> int:
    """Whole business days strictly after bar calendar date up to ref calendar date."""
    try:
        b = pd.Timestamp(bar_date).normalize()
        r = pd.Timestamp(ref_date).normalize()
    except Exception:
        return 999
    if r.date() <= b.date():
        return 0
    try:
        start = (b + timedelta(days=1)).strftime("%Y-%m-%d")
        end_excl = (r + timedelta(days=1)).strftime("%Y-%m-%d")
        return int(np.busday_count(start, end_excl))
    except Exception:
        return 999
