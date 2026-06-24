"""vol_signal contract and trust mapping."""
from __future__ import annotations

from vol_shield.domain.data_freshness import trust_from_gate
from vol_shield.services.build_shield_signal import public_vol_signal


def test_trust_from_gate_fatal():
    assert trust_from_gate({"ok": False, "tier": "FATAL"}) == "FATAL"


def test_trust_from_gate_high():
    assert trust_from_gate({"ok": True, "tier": None}, {"shield_fetch_error": None}) == "HIGH"


def test_public_vol_signal_keys():
    row = {
        "as_of": "2026-06-20",
        "vix_shock": True,
        "ovx_shock": False,
        "dxy_trend": "NEUTRAL",
        "bond_liq_shock": False,
        "shield_active": True,
        "trust": "HIGH",
        "gate_tier": None,
        "computed_at": "2026-06-20T12:00:00Z",
        "shield": {},
        "gate": {},
    }
    pub = public_vol_signal(row)
    assert set(pub.keys()) == {
        "as_of",
        "vix_shock",
        "ovx_shock",
        "dxy_trend",
        "bond_liq_shock",
        "shield_active",
        "trust",
        "gate_tier",
        "computed_at",
    }
