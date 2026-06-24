"""Massive ^VIX routing with Yahoo fallback."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from vol_shield.providers.price_source import history_close_series, massive_price_enabled


@patch("vol_shield.providers.price_source.yahoo_close")
@patch("vol_shield.providers.price_source.massive_history_close_series")
@patch("vol_shield.providers.price_source.massive_price_enabled", return_value=True)
def test_massive_primary_for_vix(mock_enabled, mock_massive, mock_yahoo):
    idx = pd.date_range("2026-01-01", periods=5, freq="B")
    mock_massive.return_value = pd.Series([20.0, 21.0, 22.0, 23.0, 24.0], index=idx)
    s = history_close_series("^VIX", period="60d")
    assert len(s) == 5
    mock_massive.assert_called_once()
    mock_yahoo.assert_not_called()


@patch("vol_shield.providers.price_source.yahoo_close")
@patch("vol_shield.providers.price_source.massive_history_close_series")
@patch("vol_shield.providers.price_source.massive_price_enabled", return_value=True)
def test_yahoo_fallback_when_massive_empty(mock_enabled, mock_massive, mock_yahoo):
    mock_massive.return_value = pd.Series(dtype=float)
    idx = pd.date_range("2026-01-01", periods=3, freq="B")
    mock_yahoo.return_value = pd.Series([18.0, 19.0, 20.0], index=idx)
    s = history_close_series("^VIX", period="60d")
    assert len(s) == 3
    mock_yahoo.assert_called_once()
