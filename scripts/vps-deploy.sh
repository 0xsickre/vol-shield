#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
git fetch origin
git pull --ff-only origin master || git pull --ff-only origin main
QS="${REPO_ROOT}/../quant-shared"
if [[ ! -d "${QS}/.git" ]]; then
  git clone https://github.com/0xsickre/quant-shared.git "${QS}"
else
  git -C "${QS}" pull --ff-only origin main
fi
"$REPO_ROOT/.venv/bin/pip" install -q -e "${QS}"
"$REPO_ROOT/.venv/bin/pip" install -q -e "$REPO_ROOT[dev]"
systemctl restart vol-shield-streamlit 2>/dev/null || true
echo "vol-shield deploy done at $(git rev-parse --short HEAD)"
