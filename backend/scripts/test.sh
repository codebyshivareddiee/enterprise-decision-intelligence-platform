#!/usr/bin/env bash
# scripts/test.sh — Run the test suite with coverage.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

echo "▶  Running tests..."
pytest --cov=app --cov-report=term-missing -v

echo "✔  Tests complete."
