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

# 0) Ensure 'uv' is available
if ! command -v uv >/dev/null 2>&1; then
  echo "✗ Error: 'uv' is required but was not found in PATH." >&2
  echo "  Install with Homebrew: brew install uv" >&2
  exit 1
fi

# 1) Create and activate virtual environment (via uv)
if [ ! -d "${DEPS_DIR}" ]; then
  echo "➤ Creating virtual environment at ${DEPS_DIR}…"
  uv venv "${DEPS_DIR}"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "${DEPS_DIR}/bin/activate"

# 2) Install dependencies using uv
echo "➤ Installing dependencies…"
uv pip install jinja2

# 3) Exec your script, passing along any args
exec python "${PYTHON_SCRIPT}" "$@"
