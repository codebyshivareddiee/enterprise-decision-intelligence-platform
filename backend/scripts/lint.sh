#!/usr/bin/env bash
# scripts/lint.sh — Run all linters (Ruff, Black check, mypy).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

echo "▶  Ruff lint..."
ruff check app tests

echo "▶  Ruff format check..."
ruff format --check app tests

echo "▶  Black check..."
black --check app tests

echo "▶  mypy..."
mypy app

echo "✔  All checks passed."
