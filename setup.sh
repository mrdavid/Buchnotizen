#!/usr/bin/env bash
# Create the virtual environment and install dependencies using uv.
# Run once in a new environment:
#   bash setup.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv &>/dev/null; then
    echo "Error: uv not found. Install it from https://github.com/astral-sh/uv" >&2
    exit 1
fi

uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt

echo ""
echo "Done. Activate the environment with:"
echo "  source activate.sh"
