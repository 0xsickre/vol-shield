# vol-shield

Standalone volatility / cross-asset stress domain — VIX, OVX, MOVE, DXY shield + hard freshness gate.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
vol-shield-refresh
vol-shield-signal --out snapshots/latest.json --persist
```

## Environment

| Variable | Purpose |
|----------|---------|
| `VOL_SHIELD_DATA_DIR` | Data root (default: repo root) |
| `VOL_SHIELD_DB_PATH` | SQLite file path |
| `VOL_SHIELD_SNAPSHOT_PATH` | Override `latest.json` path |

## VPS

```bash
bash scripts/vps-setup.sh
systemctl enable --now vol-shield-refresh.timer
systemctl enable --now vol-shield-deploy.timer
systemctl enable --now vol-shield-streamlit
```

Timer: Mon–Fri 07:30, 12:30, 21:00 UTC.

Consumers (macro-rates): set `VOL_SHIELD_SNAPSHOT_PATH=/var/lib/vol-shield/snapshots/latest.json` and `VOL_SHIELD_READ_SNAPSHOT=1` (default on).

## Published contract (`vol_signal`)

`as_of`, `vix_shock`, `ovx_shock`, `dxy_trend`, `bond_liq_shock`, `shield_active`, `trust`

Full shield dict + gate in snapshot JSON under `shield` / `gate`.
