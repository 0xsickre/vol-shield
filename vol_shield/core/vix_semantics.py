"""VIX thresholds and shock semantics — single source of truth."""
from __future__ import annotations

VIX_MACRO_RETENTION_LOW = 20.0
VIX_MACRO_RETENTION_HIGH = 35.0
VIX_MACRO_RETENTION_FLOOR = 0.2

VIX_PENALTY_RISK_ON_THRESHOLD = 25.0

VIX_SHIELD_LEVEL = 20.0
VIX_SHIELD_SPIKE_BASE = 15.0
VIX_SHIELD_SPIKE_RATIO = 1.12

VIX_TERM_BACKWARDATION_RATIO = 1.0


def vix_term_backwardation(
    spot: float | None,
    vix3m: float | None,
    *,
    ratio_threshold: float = VIX_TERM_BACKWARDATION_RATIO,
) -> bool:
    if spot is None or vix3m is None:
        return False
    try:
        s, m = float(spot), float(vix3m)
    except (TypeError, ValueError):
        return False
    if m <= 0:
        return False
    return (s / m) > float(ratio_threshold)


def vix_term_ratio(spot: float | None, vix3m: float | None) -> float | None:
    if spot is None or vix3m is None:
        return None
    try:
        s, m = float(spot), float(vix3m)
    except (TypeError, ValueError):
        return None
    if m <= 0:
        return None
    return round(s / m, 4)


def vix_shock_from_curr_prev(curr: float | None, prev: float | None) -> bool:
    if curr is None or prev is None:
        return False
    try:
        c, p = float(curr), float(prev)
    except (TypeError, ValueError):
        return False
    if p <= 0:
        return c > VIX_SHIELD_LEVEL
    return (c > VIX_SHIELD_LEVEL) or (c > VIX_SHIELD_SPIKE_BASE and (c / p) > VIX_SHIELD_SPIKE_RATIO)


def vix_shock_combined(
    curr: float | None,
    prev: float | None,
    vix3m: float | None = None,
) -> bool:
    return vix_shock_from_curr_prev(curr, prev) or vix_term_backwardation(curr, vix3m)


def macro_retention_multiplier_from_vix(vix: float | None) -> float:
    try:
        x = float(vix if vix is not None else VIX_MACRO_RETENTION_LOW)
    except (TypeError, ValueError):
        x = VIX_MACRO_RETENTION_LOW
    if x <= VIX_MACRO_RETENTION_LOW:
        return 1.0
    if x >= VIX_MACRO_RETENTION_HIGH:
        return float(VIX_MACRO_RETENTION_FLOOR)
    span = VIX_MACRO_RETENTION_HIGH - VIX_MACRO_RETENTION_LOW
    return 1.0 - ((x - VIX_MACRO_RETENTION_LOW) / span) * (1.0 - VIX_MACRO_RETENTION_FLOOR)


def macro_retention_multiplier_from_shield(shield: dict | None) -> float:
    if not shield:
        return 1.0
    try:
        vix = float(shield.get("VIX_Value", VIX_MACRO_RETENTION_LOW) or VIX_MACRO_RETENTION_LOW)
    except (TypeError, ValueError):
        vix = VIX_MACRO_RETENTION_LOW
    return macro_retention_multiplier_from_vix(vix)
