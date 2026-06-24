#!/usr/bin/env bash
# Idempotent VPS setup for vol-shield (SQLite + systemd timers + Streamlit).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="/var/lib/vol-shield"
ENV_FILE="${REPO_ROOT}/.env"
VENV="${REPO_ROOT}/.venv"

log() { echo "[vps-setup] $*"; }

log "Creating data directories..."
mkdir -p "${DATA_DIR}/snapshots"

if [[ ! -f "${ENV_FILE}" ]]; then
  log "Creating .env from deploy/env.example..."
  cp "${REPO_ROOT}/deploy/env.example" "${ENV_FILE}"
  log "Edit ${ENV_FILE} — set MASSIVE_API_KEY if using Massive for ^VIX."
fi

if [[ ! -d "${VENV}" ]]; then
  log "Creating Python venv..."
  python3 -m venv "${VENV}"
fi

log "Installing package..."
"${VENV}/bin/pip" install -q --upgrade pip
"${VENV}/bin/pip" install -q -e "${REPO_ROOT}[dev]"

if [[ ! -f "${DATA_DIR}/snapshots/latest.json" ]]; then
  log "Running initial vol-shield-refresh + signal..."
  set -a
  # shellcheck source=/dev/null
  source "${ENV_FILE}"
  set +a
  "${VENV}/bin/vol-shield-refresh"
  "${VENV}/bin/vol-shield-signal" --out "${DATA_DIR}/snapshots/latest.json" --persist
else
  log "Snapshot already exists, skipping initial refresh."
fi

log "Installing systemd units..."
cp "${REPO_ROOT}/deploy/systemd/"* /etc/systemd/system/
chmod +x "${REPO_ROOT}/scripts/vps-deploy.sh"
systemctl daemon-reload
systemctl enable vol-shield-refresh.timer vol-shield-deploy.timer vol-shield-streamlit
systemctl start vol-shield-refresh.timer vol-shield-deploy.timer
systemctl restart vol-shield-streamlit

echo ""
echo "=== vol-shield setup complete ==="
systemctl list-timers vol-shield-refresh.timer vol-shield-deploy.timer --no-pager || true
echo ""
echo "Dashboard: https://shield.kresicds.com (after DNS A -> VPS IP)"
echo "Snapshot:  ${DATA_DIR}/snapshots/latest.json"
