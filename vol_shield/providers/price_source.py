"""Unified price router — Massive for ^VIX when enabled, Yahoo fallback."""
from __future__ import annotations

from typing import Any

import pandas as pd

from vol_shield.core.reference_data import massive_symbol_for
from vol_shield.platform.secrets import get_secret
from vol_shield.providers.massive_history import massive_history_close_series
from vol_shield.providers.yahoo_history import history_close_series as yahoo_close


def massive_price_enabled() -> bool:
    key = (get_secret("MASSIVE_API_KEY", "") or "").strip()
    if not key:
        return False
    flag = str(get_secret("MASSIVE_PRICE_ENABLED", "1") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def history_close_series(
    ticker: str,
    *,
    start: Any = None,
    end: Any = None,
    period: str | None = None,
    interval: str = "1d",
    auto_adjust: bool = True,
) -> pd.Series:
    sym = str(ticker or "").strip()
    if not sym:
        return pd.Series(dtype=float)

    massive_sym = massive_symbol_for(sym)
    if massive_price_enabled() and massive_sym:
        try:
            s = massive_history_close_series(
                sym,
                start=start,
                end=end,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
            )
            if s is not None and not s.empty:
                return s
        except Exception:
            pass

    return yahoo_close(
        sym,
        start=start,
        end=end,
        period=period,
        interval=interval,
        auto_adjust=auto_adjust,
    )
