#!/usr/bin/env bash
# Build the React frontend and start the Treasure Runner web server.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Building C backend (if needed)..."
make dist 2>/dev/null || {
  echo "Warning: C build failed or make unavailable. Ensure dist/libbackend.so exists."
}

echo "==> Installing Python web dependencies..."
pip install -q -r python/requirements-web.txt

echo "==> Building React frontend..."
cd web
npm install
npm run build
cd ..

CONFIG="${TREASURE_RUNNER_CONFIG:-$ROOT/assets/starter.ini}"
echo "==> Starting server on http://0.0.0.0:8000"
echo "    World config: $CONFIG"
cd python
python run_server.py --host 0.0.0.0 --port 8000 --config "$CONFIG"
