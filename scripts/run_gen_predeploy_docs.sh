#!/usr/bin/env bash
set -euo pipefail

# ─── CONFIG ──────────────────────────────────────────────────────────────────────
# Directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Your requirements file and python entrypoint
PYTHON_SCRIPT="${SCRIPT_DIR}/gen_predeploy_docs.py"

# Where to install deps
DEPS_DIR="${SCRIPT_DIR}/.venv"
# ────────────────────────────────────────────────────────────────────────────────

# 1) Create and activate virtual environment
if [ ! -d "${DEPS_DIR}" ]; then
  echo "➤ Creating virtual environment at ${DEPS_DIR}…"
  python3 -m venv "${DEPS_DIR}"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "${DEPS_DIR}/bin/activate"

# 2) Upgrade pip and install dependencies
echo "➤ Upgrading pip…"
pip install --upgrade pip

echo "➤ Installing dependencies…"
pip install jinja2

# 3) Exec your script, passing along any args
exec python "${PYTHON_SCRIPT}" "$@"
