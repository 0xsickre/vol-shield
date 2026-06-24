"""Shield engine smoke with mocked prices."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from vol_shield.domain.shield_engine import get_global_shield_status


def _mock_frame():
    idx = pd.date_range("2026-01-01", periods=30, freq="B")
    return pd.DataFrame(
        {
            "^VIX": [18.0 + i * 0.1 for i in range(30)],
            "^VIX3M": [19.0 + i * 0.05 for i in range(30)],
            "DX-Y.NYB": [104.0 + i * 0.02 for i in range(30)],
            "^OVX": [35.0 + i * 0.1 for i in range(30)],
            "^MOVE": [90.0 + i * 0.5 for i in range(30)],
        },
        index=idx,
    )


@patch("vol_shield.domain.shield_engine._shield_close_frame")
def test_shield_active_on_high_move(mock_frame):
    df = _mock_frame()
    df.iloc[-1, df.columns.get_loc("^MOVE")] = 125.0
    mock_frame.return_value = (df, None)
    out = get_global_shield_status(yahoo_fence="test")
    assert out["BOND_LIQUIDITY_SHOCK"] is True
    assert out["Shield_Active"] is True
