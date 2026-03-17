#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/publish.sh \"commit message\""
  exit 1
fi

COMMIT_MESSAGE="$1"

if [[ -x "${ROOT}/.venv/bin/panel" ]]; then
  PANEL_BIN="${ROOT}/.venv/bin/panel"
else
  PANEL_BIN="panel"
fi

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT}/.venv/bin/python"
else
  PYTHON_BIN="python"
fi

echo "Rebuilding static site..."
rm -rf docs
mkdir -p docs/app
"${PANEL_BIN}" convert app.py --to pyodide-worker --out docs/app
"${PYTHON_BIN}" scripts/prepare_static_export.py

echo
echo "Current git status:"
git status --short

echo
echo "Staging changes..."
git add .

if git diff --cached --quiet; then
  echo "No staged changes to commit."
  exit 0
fi

echo
echo "Creating commit..."
git commit -m "${COMMIT_MESSAGE}"

echo
echo "Pushing to GitHub..."
git push

echo
echo "Done."
