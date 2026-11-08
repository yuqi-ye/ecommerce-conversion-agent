#!/bin/zsh
set -eu
project_root="$(cd "$(dirname "$0")/.." && pwd)"
exec "$project_root/.venv/bin/python" "$project_root/agent/run_compare.py" "$@"
