"""Map hard gate result to vol_signal trust badge."""
from __future__ import annotations

from typing import Any

import pandas as pd


def snapshot_age_hours(computed_at: str | None) -> float | None:
    if not computed_at:
        return None
    try:
        ts = pd.Timestamp(computed_at)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        now = pd.Timestamp.now(tz="UTC")
        return float((now - ts).total_seconds() / 3600.0)
    except Exception:
        return None


def is_snapshot_stale(computed_at: str | None, *, max_hours: float = 6.0) -> bool:
    age = snapshot_age_hours(computed_at)
    if age is None:
        return True
    return age > float(max_hours)


def trust_from_gate(gate: dict[str, Any], shield: dict[str, Any] | None = None) -> str:
    tier = gate.get("tier")
    if tier == "FATAL":
        return "FATAL"
    if tier == "CRITICAL_STALE":
        return "CRITICAL_STALE"
    sh = shield or {}
    if sh.get("shield_fetch_error"):
        return "MEDIUM"
    if gate.get("ok"):
        return "HIGH"
    return "LOW"
