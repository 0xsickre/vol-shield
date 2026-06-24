"""Vol shield Streamlit dashboard — port 8503."""
from __future__ import annotations

import json
import os

import streamlit as st

from vol_shield.data.repositories.shield_repository import insert_shield_snapshot, upsert_shield_signal
from vol_shield.platform.settings import default_snapshot_path
from vol_shield.services.build_shield_signal import build_shield_signal, public_vol_signal


def _load_snapshot() -> dict:
    path = default_snapshot_path()
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


st.set_page_config(page_title="Vol Shield", layout="wide")
st.title("Vol Shield")
st.caption("VIX / OVX / MOVE / DXY stress indices + hard freshness gate")

snap = _load_snapshot()
if st.button("Refresh now"):
    try:
        row = build_shield_signal()
        snap = {**public_vol_signal(row), "shield": row.get("shield"), "gate": row.get("gate")}
        upsert_shield_signal(row)
        insert_shield_snapshot(snap, as_of=snap.get("as_of"))
        path = default_snapshot_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, default=str)
        st.success(f"Updated {path} (persisted)")
    except Exception as e:
        st.error(str(e))

if not snap:
    st.warning("No snapshot — run vol-shield-signal or click Refresh")
    st.stop()

shield = snap.get("shield") or {}
gate = snap.get("gate") or {}

c1, c2, c3, c4 = st.columns(4)
c1.metric("VIX", f"{shield.get('VIX_Value', '—')}")
c2.metric("MOVE", f"{shield.get('MOVE_Value', '—')}")
c3.metric("DXY trend", shield.get("DXY_Trend", "—"))
c4.metric("Trust", snap.get("trust", "—"))

st.metric("Shield Active", str(snap.get("shield_active", shield.get("Shield_Active"))))
st.caption(f"As of {snap.get('as_of')} · computed {snap.get('computed_at', '—')}")

if gate.get("per_ticker"):
    st.subheader("Gate per ticker")
    st.dataframe(
        [{"ticker": k, **v} for k, v in gate["per_ticker"].items()],
        use_container_width=True,
    )

if gate.get("reasons"):
    st.warning("Gate reasons: " + "; ".join(gate["reasons"]))

with st.expander("Full shield payload"):
    st.json(shield)
