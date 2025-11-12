#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5173}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies with npm install..."
  npm install
fi

echo "Launching Vite dev server from $FRONTEND_DIR"
echo "Use your IDE's forwarded port interface or open http://127.0.0.1:${PORT}/ to preview."

echo "Press Ctrl+C to stop the server."

npm run dev -- --host 0.0.0.0 --port "$PORT"
