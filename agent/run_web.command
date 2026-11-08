#!/bin/zsh
set -eu
project_root="$(cd "$(dirname "$0")/.." && pwd)"
exec "$project_root/.venv/bin/python" -m streamlit run "$project_root/agent/web_app.py" --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
