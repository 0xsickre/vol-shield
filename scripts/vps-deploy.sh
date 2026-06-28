#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

git_repo() {
  git -c "safe.directory=${1}" -C "${1}" "${@:2}"
}

cd "$REPO_ROOT"
git_repo "${REPO_ROOT}" fetch origin
git_repo "${REPO_ROOT}" pull --ff-only origin master || git_repo "${REPO_ROOT}" pull --ff-only origin main
QS="${REPO_ROOT}/../quant-shared"
if [[ ! -d "${QS}/.git" ]]; then
  git clone https://github.com/0xsickre/quant-shared.git "${QS}"
else
  git_repo "${QS}" pull --ff-only origin main
fi
"$REPO_ROOT/.venv/bin/pip" install -q -e "${QS}"
"$REPO_ROOT/.venv/bin/pip" install -q -e "$REPO_ROOT[dev]"
systemctl restart vol-shield-streamlit 2>/dev/null || true
echo "vol-shield deploy done at $(git_repo "${REPO_ROOT}" rev-parse --short HEAD)"
