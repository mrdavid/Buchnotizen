#!/usr/bin/env bash
# Source this script to activate the project virtual environment:
#   source activate.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
echo "Activated: $VIRTUAL_ENV"
