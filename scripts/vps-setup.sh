#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${VOL_SHIELD_DATA_DIR:-/var/lib/vol-shield}"
mkdir -p "$DATA_DIR/snapshots"
if [[ ! -f "$REPO_ROOT/.env" ]]; then
  cp "$REPO_ROOT/deploy/env.example" "$REPO_ROOT/.env"
fi
python3 -m venv "$REPO_ROOT/.venv" 2>/dev/null || true
"$REPO_ROOT/.venv/bin/pip" install -q -e "$REPO_ROOT[dev]"
cp "$REPO_ROOT/deploy/systemd/"* /etc/systemd/system/
systemctl daemon-reload
echo "vol-shield vps-setup complete"
