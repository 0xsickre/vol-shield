"""VIX semantics unit tests."""
from __future__ import annotations

from vol_shield.core.vix_semantics import (
    VIX_MACRO_RETENTION_HIGH,
    VIX_MACRO_RETENTION_LOW,
    macro_retention_multiplier_from_vix,
    vix_shock_from_curr_prev,
    vix_term_backwardation,
    vix_term_ratio,
)


def test_macro_retention_endpoints():
    assert macro_retention_multiplier_from_vix(VIX_MACRO_RETENTION_LOW) == 1.0
    assert macro_retention_multiplier_from_vix(VIX_MACRO_RETENTION_HIGH) == 0.2
    assert 0.2 < macro_retention_multiplier_from_vix(27.5) < 1.0


def test_vix_shock_spike():
    assert vix_shock_from_curr_prev(16.0, 14.0) is True
    assert vix_shock_from_curr_prev(21.0, 20.0) is True
    assert vix_shock_from_curr_prev(18.0, 17.0) is False


def test_vix_term_backwardation():
    assert vix_term_backwardation(25.0, 20.0) is True
    assert vix_term_ratio(20.0, 22.0) is not None
