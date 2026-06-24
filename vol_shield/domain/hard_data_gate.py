"""Hard freshness gate for critical macro tickers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from vol_shield.core.reference_data import CRITICAL_MACRO_TICKERS
from vol_shield.platform.busday import business_day_gap, series_last_ts, staleness_hours

MAX_BUSINESS_DAY_GAP = 2
SAME_DAY_MAX_HOURS = 24.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def evaluate_hard_macro_data_gate(
    *,
    shield_data: dict[str, Any] | None,
    copper_series: pd.Series | None = None,
    ref_utc: datetime | None = None,
) -> dict[str, Any]:
    try:
        return _evaluate_impl(shield_data=shield_data, copper_series=copper_series, ref_utc=ref_utc)
    except Exception as e:
        return {
            "ok": True,
            "tier": None,
            "reasons": [f"hard_gate_eval_exception:{type(e).__name__}"],
            "per_ticker": {},
            "ref_utc": (ref_utc or _utc_now()).isoformat(),
            "max_business_day_gap_rule": MAX_BUSINESS_DAY_GAP,
            "gate_error": str(e)[:200],
        }


def _evaluate_impl(
    *,
    shield_data: dict[str, Any] | None,
    copper_series: pd.Series | None,
    ref_utc: datetime | None,
) -> dict[str, Any]:
    ref = ref_utc or _utc_now()
    ref_date = ref.date()
    sh = shield_data if isinstance(shield_data, dict) else {}

    per_ticker: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []

    cu_ts = series_last_ts(copper_series if isinstance(copper_series, pd.Series) else None)
    hg_gap = business_day_gap(cu_ts, ref_date) if cu_ts is not None else 999
    hg_hours = staleness_hours(cu_ts, ref)
    per_ticker["HG=F"] = {
        "last_updated": str(cu_ts.date()) if cu_ts is not None else None,
        "business_day_gap": hg_gap,
        "hours_since_bar": hg_hours,
    }
    if cu_ts is None:
        reasons.append("critical_missing:HG=F")
    elif hg_gap >= MAX_BUSINESS_DAY_GAP:
        reasons.append(f"critical_stale:HG=F gap_bd={hg_gap}")
    elif cu_ts.normalize().date() == ref_date and hg_hours is not None and hg_hours > SAME_DAY_MAX_HOURS:
        reasons.append(f"critical_stale:HG=F same_day_hours={hg_hours:.1f}")

    y_ts_raw = sh.get("yahoo_last_bar_ts")
    y_ts = pd.Timestamp(y_ts_raw) if y_ts_raw is not None and str(y_ts_raw).strip() else None
    if y_ts is not None and y_ts.tzinfo is not None:
        y_ts = y_ts.tz_convert("UTC").tz_localize(None)

    fetch_err = sh.get("shield_fetch_error")
    if y_ts is not None:
        gap_bd = business_day_gap(y_ts, ref_date)
        hrs = staleness_hours(y_ts, ref)
        for sym in ("^VIX", "^MOVE", "DX-Y.NYB"):
            per_ticker[sym] = {
                "last_updated": str(y_ts.date()),
                "business_day_gap": gap_bd,
                "hours_since_bar": hrs,
            }
        if gap_bd >= MAX_BUSINESS_DAY_GAP:
            reasons.append(f"critical_stale:shield_bundle gap_bd={gap_bd}")
        elif y_ts.normalize().date() == ref_date and hrs is not None and hrs > SAME_DAY_MAX_HOURS:
            reasons.append(f"critical_stale:shield_bundle same_day_hours={hrs:.1f}")
    else:
        for sym in ("^VIX", "^MOVE", "DX-Y.NYB"):
            per_ticker[sym] = {"last_updated": None, "business_day_gap": None, "hours_since_bar": None}
        if fetch_err and str(fetch_err).strip():
            reasons.append("critical_shield_fetch_failed")
        else:
            reasons.append("critical_missing:shield_timestamps")

    ok = len(reasons) == 0
    tier = None
    if not ok:
        if any(r.startswith("critical_missing") for r in reasons) or any(
            r == "critical_shield_fetch_failed" for r in reasons
        ):
            tier = "FATAL"
        else:
            tier = "CRITICAL_STALE"

    return {
        "ok": ok,
        "tier": tier,
        "reasons": reasons,
        "per_ticker": per_ticker,
        "ref_utc": ref.isoformat(),
        "max_business_day_gap_rule": MAX_BUSINESS_DAY_GAP,
        "critical_tickers": list(CRITICAL_MACRO_TICKERS),
    }
