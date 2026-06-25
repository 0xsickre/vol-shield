"""Vol-shield stress scenario tests (deterministic, no network)."""
from __future__ import annotations

import pandas as pd
import pytest

from vol_shield.core.vix_semantics import (
    VIX_MACRO_RETENTION_HIGH,
    macro_retention_multiplier_from_vix,
    vix_shock_from_curr_prev,
    vix_term_backwardation,
    vix_term_ratio,
)
from vol_shield.domain.shield_engine import (
    BOND_LIQUIDITY_MOVE_THRESHOLD,
    get_global_shield_status,
)

pytestmark = pytest.mark.stress


@pytest.mark.parametrize(
    "curr, prev, expected",
    [
        (16.0, 14.0, True),
        (21.0, 20.0, True),
        (18.0, 17.0, False),
    ],
    ids=["V01_spike", "V02_level", "V03_no_spike"],
)
def test_vix_shock_semantics(curr, prev, expected):
    assert vix_shock_from_curr_prev(curr, prev) is expected


def test_vix_term_backwardation_v03():
    assert vix_term_backwardation(25.0, 20.0) is True
    assert vix_term_ratio(20.0, 22.0) is not None


def test_macro_retention_v05():
    assert macro_retention_multiplier_from_vix(VIX_MACRO_RETENTION_HIGH) == pytest.approx(0.2)
    assert macro_retention_multiplier_from_vix(40.0) == pytest.approx(0.2)


def _shield_frame(vix=15.0, ovx=30.0, move=90.0, dxy=104.0) -> pd.DataFrame:
    idx = pd.bdate_range(end="2024-06-14", periods=10)
    n = len(idx)

    def series(final: float, penultimate: float | None = None) -> list[float]:
        prev = penultimate if penultimate is not None else final - 1.0
        return [prev] * (n - 1) + [final]

    return pd.DataFrame(
        {
            "^VIX": series(vix, vix - 1.0),
            "^VIX3M": series(vix + 2.0, vix + 1.0),
            "^OVX": series(ovx, ovx * 0.9),
            "^MOVE": series(move, move - 5.0),
            "DX-Y.NYB": series(dxy, dxy - 0.2),
            "CL=F": series(81.0, 80.0),
            "BZ=F": series(85.0, 84.0),
            "HG=F": series(4.6, 4.5),
            "^GSPC": series(5320.0, 5300.0),
            "GC=F": series(2310.0, 2300.0),
            "TLT": series(92.5, 92.0),
            "^IRX": [5.2] * n,
        },
        index=idx,
    )


@pytest.fixture(autouse=True)
def _clear_shield_cache():
    get_global_shield_status.clear()
    yield
    get_global_shield_status.clear()


@pytest.mark.parametrize(
    "move, expected_bond_shock",
    [(125.0, True), (90.0, False)],
    ids=["V04_move_shock", "V04_calm"],
)
def test_bond_liquidity_threshold(move, expected_bond_shock, monkeypatch):
    monkeypatch.setattr(
        "vol_shield.domain.shield_engine._shield_close_frame",
        lambda asof_date=None: (_shield_frame(move=move), None),
    )
    out = get_global_shield_status()
    assert out["BOND_LIQUIDITY_SHOCK"] is expected_bond_shock
    if expected_bond_shock:
        assert float(out["MOVE_Value"]) > BOND_LIQUIDITY_MOVE_THRESHOLD


@pytest.mark.parametrize(
    "vix, ovx, move, expect_shield",
    [
        (15.0, 30.0, 90.0, False),
        (28.0, 35.0, 90.0, True),
        (45.0, 90.0, 150.0, True),
    ],
    ids=["S00_calm", "S05_moderate", "S06_extreme"],
)
def test_shield_status_scenarios(vix, ovx, move, expect_shield, monkeypatch):
    monkeypatch.setattr(
        "vol_shield.domain.shield_engine._shield_close_frame",
        lambda asof_date=None: (_shield_frame(vix=vix, ovx=ovx, move=move), None),
    )
    out = get_global_shield_status()
    assert out["VIX_Value"] == pytest.approx(vix, abs=1.5)
    assert out["Shield_Active"] is expect_shield
