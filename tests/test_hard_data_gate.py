"""Hard data gate tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from vol_shield.domain.hard_data_gate import evaluate_hard_macro_data_gate


def _series_with_last_date(last_date):
    idx = pd.to_datetime([last_date])
    return pd.Series([1.0], index=idx)


def test_hard_gate_ok_fresh_shield_and_copper():
    ref = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
    sh = {"yahoo_last_bar_ts": pd.Timestamp("2026-03-27 10:00:00")}
    cu = _series_with_last_date("2026-03-27")
    out = evaluate_hard_macro_data_gate(shield_data=sh, copper_series=cu, ref_utc=ref)
    assert out["ok"] is True
    assert out["tier"] is None


def test_hard_gate_critical_stale_business_days():
    ref = datetime(2026, 3, 31, 12, 0, 0, tzinfo=timezone.utc)
    sh = {"yahoo_last_bar_ts": pd.Timestamp("2026-03-26 16:00:00")}
    cu = _series_with_last_date("2026-03-26")
    out = evaluate_hard_macro_data_gate(shield_data=sh, copper_series=cu, ref_utc=ref)
    assert out["ok"] is False
    assert out["tier"] == "CRITICAL_STALE"


def test_hard_gate_fatal_missing_copper():
    ref = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
    sh = {"yahoo_last_bar_ts": pd.Timestamp("2026-03-27 10:00:00")}
    out = evaluate_hard_macro_data_gate(
        shield_data=sh, copper_series=pd.Series(dtype=float), ref_utc=ref
    )
    assert out["ok"] is False
    assert out["tier"] == "FATAL"


def test_hard_gate_fatal_shield_fetch():
    ref = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
    cu = _series_with_last_date("2026-03-27")
    sh = {"shield_fetch_error": "empty", "yahoo_last_bar_ts": None}
    out = evaluate_hard_macro_data_gate(shield_data=sh, copper_series=cu, ref_utc=ref)
    assert out["ok"] is False
    assert out["tier"] == "FATAL"
