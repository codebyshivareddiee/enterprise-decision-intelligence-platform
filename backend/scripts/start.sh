#!/usr/bin/env bash
# scripts/start.sh — Start the backend development server locally (no Docker).
# Assumes uv is installed and a virtual environment exists at .venv/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

if [ ! -f ".env" ]; then
    echo "⚠  No .env found — copying .env.example to .env"
    cp .env.example .env
fi

echo "▶  Starting backend (uvicorn hot-reload)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
