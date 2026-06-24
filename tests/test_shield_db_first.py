"""DB-first shield close frame without live Yahoo."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from vol_shield.domain.shield_engine import _shield_close_frame


def _series(vals):
    idx = pd.date_range("2026-01-01", periods=len(vals), freq="B")
    return pd.Series(vals, index=idx, dtype=float)


@patch("vol_shield.domain.shield_engine.history_close_series")
@patch("vol_shield.domain.shield_engine.load_price_series")
def test_db_first_skips_live_when_db_has_bars(mock_load, mock_live):
    mock_load.side_effect = lambda sym, limit=120: {
        "^VIX": _series([18.0, 19.0, 20.0]),
        "^VIX3M": _series([19.0, 19.5, 20.0]),
        "DX-Y.NYB": _series([104.0, 104.5, 105.0]),
        "^OVX": _series([35.0, 36.0, 37.0]),
        "^MOVE": _series([90.0, 91.0, 92.0]),
    }.get(sym, pd.Series(dtype=float))

    df, err = _shield_close_frame()
    assert not df.empty
    assert err is None
    mock_live.assert_not_called()


@patch("vol_shield.domain.shield_engine.history_close_series")
@patch("vol_shield.domain.shield_engine.load_price_series")
def test_partial_tickers_flag(mock_load, mock_live):
    mock_load.return_value = pd.Series(dtype=float)
    mock_live.side_effect = lambda sym, **kw: {
        "^VIX": _series([18.0, 19.0]),
        "^VIX3M": _series([19.0, 19.5]),
    }.get(sym, pd.Series(dtype=float))

    df, err = _shield_close_frame()
    assert not df.empty
    assert err == "partial_tickers"
