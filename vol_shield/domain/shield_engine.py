from __future__ import annotations

from datetime import timedelta

import pandas as pd
from typing import Dict, Optional, Tuple

from vol_shield.core.reference_data import SHIELD_TICKERS
from vol_shield.core.vix_semantics import vix_shock_combined, vix_term_ratio
from vol_shield.data.repositories.price_repository import load_price_series
from vol_shield.domain.calendar_engine import fomc_shield_fields
from vol_shield.domain.yahoo_refresh_session import yahoo_streamlit_cache_fence
from vol_shield.platform.cache import memoize
from vol_shield.platform.live_config import STREAMLIT_YAHOO_CACHE_TTL_SEC
from vol_shield.providers.price_source import history_close_series

_MIN_BARS = 2
_PARTIAL_TICKER_THRESHOLD = 3

_DEFAULT_VIX = 20.0
BOND_LIQUIDITY_MOVE_THRESHOLD = 120.0

_FOMC_INACTIVE = {
    "FOMC_Window_Active": False,
    "FOMC_Meeting_Start": None,
    "FOMC_Meeting_End": None,
    "FOMC_RiskOn_Shrink": 1.0,
}


def _fomc_fields(asof_date=None) -> dict:
    fomc = fomc_shield_fields(asof_date)
    return {
        "FOMC_Window_Active": bool(fomc.get("active")),
        "FOMC_Meeting_Start": fomc.get("meeting_start"),
        "FOMC_Meeting_End": fomc.get("meeting_end"),
        "FOMC_RiskOn_Shrink": float(fomc.get("shrink", 1.0)),
    }


def _sanitize_vix_value(v):
    if v is None:
        return _DEFAULT_VIX
    try:
        x = float(v)
    except (TypeError, ValueError):
        return _DEFAULT_VIX
    if x <= 0.0 or x > 200.0:
        return _DEFAULT_VIX
    return round(x, 2)


def _live_close_series(sym: str, asof_date=None) -> pd.Series:
    if asof_date is not None:
        asof_ts = pd.to_datetime(asof_date, errors="coerce")
        if pd.notna(asof_ts):
            if getattr(asof_ts, "tzinfo", None) is not None:
                asof_ts = asof_ts.tz_convert(None)
            end_dt = asof_ts + timedelta(days=1)
            start_dt = asof_ts - timedelta(days=60)
            return history_close_series(sym, start=start_dt, end=end_dt, interval="1d")
    return history_close_series(sym, period="60d", interval="1d")


def _ticker_close_series(sym: str, asof_date=None) -> pd.Series:
    s = load_price_series(sym, limit=120)
    if s is not None and len(s) >= _MIN_BARS:
        return s
    try:
        live = _live_close_series(sym, asof_date)
        if live is not None and not live.empty:
            return live
    except Exception:
        pass
    return pd.Series(dtype=float)


def _shield_close_frame(asof_date=None) -> Tuple[pd.DataFrame, Optional[str]]:
    series_map: Dict[str, pd.Series] = {}
    for sym in SHIELD_TICKERS:
        try:
            s = _ticker_close_series(sym, asof_date)
            if s is not None and not s.empty:
                series_map[sym] = s
        except Exception:
            continue

    if not series_map:
        return pd.DataFrame(), "no_series"

    df = pd.DataFrame(series_map).sort_index().ffill()
    if asof_date is not None:
        asof_ts = pd.to_datetime(asof_date, errors="coerce")
        if pd.notna(asof_ts):
            if getattr(asof_ts, "tzinfo", None) is not None:
                asof_ts = asof_ts.tz_convert(None)
            df = df[df.index <= asof_ts]

    df = df.dropna(how="all")
    if df.empty:
        return pd.DataFrame(), "empty_after_slice"

    fetch_err: Optional[str] = None
    if len(series_map) < _PARTIAL_TICKER_THRESHOLD:
        fetch_err = "partial_tickers"
    return df, fetch_err


@memoize(ttl=STREAMLIT_YAHOO_CACHE_TTL_SEC, show_spinner=False)
def get_global_shield_status(asof_date=None, yahoo_fence: Optional[str] = None):
    try:
        if yahoo_fence is None:
            yahoo_fence = yahoo_streamlit_cache_fence()
        _ = yahoo_fence

        close_data, fetch_err = _shield_close_frame(asof_date)
        if close_data.empty:
            return {
                "VIX_Shock": False,
                "VIX_Term_Backwardation": False,
                "VIX_Term_Ratio": None,
                "VIX3M_Value": _DEFAULT_VIX,
                "DXY_Trend": "NEUTRAL",
                "OVX_Shock": False,
                "VIX_Value": _DEFAULT_VIX,
                "DXY_Value": 0.0,
                "OVX_Value": 0.0,
                "MOVE_Value": 0.0,
                "BOND_LIQUIDITY_SHOCK": False,
                "Shield_Active": False,
                "yahoo_bar_asof": None,
                "yahoo_last_bar_ts": None,
                "shield_fetch_error": fetch_err or "empty",
                **_fomc_fields(asof_date),
            }

        _bar_ts = close_data.index.max()
        try:
            yahoo_bar_asof = str(pd.Timestamp(_bar_ts).date())
            yahoo_last_bar_ts = pd.Timestamp(_bar_ts)
            if yahoo_last_bar_ts.tzinfo is not None:
                yahoo_last_bar_ts = yahoo_last_bar_ts.tz_convert("UTC").tz_localize(None)
        except Exception:
            yahoo_bar_asof = None
            yahoo_last_bar_ts = None

        def get_safe_series(ticker):
            if ticker in close_data.columns:
                series = close_data[ticker].dropna()
                if len(series) >= 2:
                    return float(series.iloc[-1]), float(series.iloc[-2])
            return None, None

        vix_curr, vix_prev = get_safe_series("^VIX")
        vix3m_curr, _ = get_safe_series("^VIX3M")
        vix3m_val = round(float(vix3m_curr), 2) if vix3m_curr is not None else None
        vix_term_ratio_val = vix_term_ratio(vix_curr, vix3m_curr)
        vix_term_back = bool(
            vix_curr is not None
            and vix3m_curr is not None
            and vix_term_ratio_val is not None
            and float(vix_term_ratio_val) > 1.0
        )
        vix_shock = vix_shock_combined(vix_curr, vix_prev, vix3m_curr)

        dxy_curr, dxy_prev = get_safe_series("DX-Y.NYB")
        dxy_trend = "NEUTRAL"
        if dxy_curr is not None and dxy_prev is not None:
            dxy_series = close_data["DX-Y.NYB"].dropna() if "DX-Y.NYB" in close_data.columns else None
            dxy_sigma = (
                float(dxy_series.diff().dropna().tail(20).std())
                if dxy_series is not None and len(dxy_series) >= 6
                else 0.0
            )
            dxy_thr = max(0.20, 0.5 * abs(dxy_sigma))
            if dxy_curr > dxy_prev + dxy_thr:
                dxy_trend = "BULLISH"
            elif dxy_curr < dxy_prev - dxy_thr:
                dxy_trend = "BEARISH"

        ovx_curr, ovx_prev = get_safe_series("^OVX")
        ovx_shock = False
        if ovx_curr is not None and ovx_prev is not None:
            ovx_shock = ovx_curr > 40 or (ovx_prev > 0 and ovx_curr / ovx_prev > 1.15)

        move_curr, _ = get_safe_series("^MOVE")
        move_val = round(float(move_curr), 2) if move_curr is not None else None
        bond_liquidity_shock = bool(
            move_val is not None and float(move_curr) > float(BOND_LIQUIDITY_MOVE_THRESHOLD)
        )

        shield_on = any([vix_shock, ovx_shock, bond_liquidity_shock])

        return {
            "VIX_Shock": vix_shock,
            "VIX_Term_Backwardation": vix_term_back,
            "VIX_Term_Ratio": vix_term_ratio_val,
            "VIX3M_Value": _sanitize_vix_value(vix3m_val),
            "DXY_Trend": dxy_trend,
            "OVX_Shock": ovx_shock,
            "VIX_Value": _sanitize_vix_value(vix_curr),
            "DXY_Value": round(dxy_curr, 2) if dxy_curr is not None else 0.0,
            "OVX_Value": round(ovx_curr, 2) if ovx_curr is not None else 0.0,
            "MOVE_Value": move_val if move_val is not None else 0.0,
            "BOND_LIQUIDITY_SHOCK": bond_liquidity_shock,
            "Shield_Active": shield_on,
            "yahoo_bar_asof": yahoo_bar_asof,
            "yahoo_last_bar_ts": yahoo_last_bar_ts,
            "shield_fetch_error": fetch_err,
            **_fomc_fields(asof_date),
        }
    except Exception:
        return {
            "VIX_Shock": False,
            "VIX_Term_Backwardation": False,
            "VIX_Term_Ratio": None,
            "VIX3M_Value": _DEFAULT_VIX,
            "DXY_Trend": "NEUTRAL",
            "OVX_Shock": False,
            "VIX_Value": _DEFAULT_VIX,
            "DXY_Value": 0.0,
            "OVX_Value": 0.0,
            "MOVE_Value": 0.0,
            "BOND_LIQUIDITY_SHOCK": False,
            "Shield_Active": False,
            "yahoo_bar_asof": None,
            "yahoo_last_bar_ts": None,
            "shield_fetch_error": "exception",
            **_FOMC_INACTIVE,
        }
