"""Build and publish vol_signal."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from vol_shield.data.repositories.price_repository import load_price_series
from vol_shield.domain.data_freshness import trust_from_gate
from vol_shield.domain.hard_data_gate import evaluate_hard_macro_data_gate
from vol_shield.domain.shield_engine import get_global_shield_status
from vol_shield.providers.price_source import history_close_series


def _fetch_copper_series() -> pd.Series:
    try:
        s = load_price_series("HG=F", limit=120)
        if s is not None and len(s) >= 2:
            return s
        s = history_close_series("HG=F", period="90d", interval="1d")
        return s if s is not None and not s.empty else pd.Series(dtype=float)
    except Exception:
        return pd.Series(dtype=float)


def build_shield_signal(*, asof_date=None, yahoo_fence: str | None = None) -> dict[str, Any]:
    get_global_shield_status.clear()
    shield = get_global_shield_status(asof_date=asof_date, yahoo_fence=yahoo_fence) or {}
    copper = _fetch_copper_series()
    gate = evaluate_hard_macro_data_gate(shield_data=shield, copper_series=copper)
    trust = trust_from_gate(gate, shield)

    as_of = shield.get("yahoo_bar_asof") or datetime.now(timezone.utc).date().isoformat()
    computed_at = datetime.now(timezone.utc).isoformat()

    vol_signal = {
        "as_of": str(as_of),
        "vix_shock": bool(shield.get("VIX_Shock")),
        "ovx_shock": bool(shield.get("OVX_Shock")),
        "dxy_trend": str(shield.get("DXY_Trend") or "NEUTRAL"),
        "bond_liq_shock": bool(shield.get("BOND_LIQUIDITY_SHOCK")),
        "shield_active": bool(shield.get("Shield_Active")),
        "trust": trust,
        "gate_tier": gate.get("tier"),
        "computed_at": computed_at,
        "shield": shield,
        "gate": gate,
    }
    return vol_signal


def public_vol_signal(row: dict[str, Any]) -> dict[str, Any]:
    return {
        k: row[k]
        for k in (
            "as_of",
            "vix_shock",
            "ovx_shock",
            "dxy_trend",
            "bond_liq_shock",
            "shield_active",
            "trust",
            "gate_tier",
            "computed_at",
        )
        if k in row
    }
