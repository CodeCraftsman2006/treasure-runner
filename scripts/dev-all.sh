#!/usr/bin/env bash
# Start API + Vite together (for dev container or local Linux testing)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f "$ROOT/assets/starter.ini" ]; then
  echo "ERROR: assets/starter.ini not found."
  exit 1
fi

if [ ! -f "$ROOT/dist/libbackend.so" ]; then
  echo "Building C backend..."
  make dist
fi

export LD_LIBRARY_PATH="$ROOT/dist:${LD_LIBRARY_PATH:-}"

python3 -m pip install -q -r python/requirements-web.txt 2>/dev/null || true
cd "$ROOT/web" && npm install --silent 2>/dev/null || true
cd "$ROOT"

cleanup() {
  kill "$API_PID" "$VITE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting API on http://localhost:8000"
cd "$ROOT/python"
python3 run_server.py --host 0.0.0.0 --port 8000 --config "$ROOT/assets/starter.ini" &
API_PID=$!

echo "Starting web UI on http://localhost:5173"
cd "$ROOT/web"
npm run dev -- --host 0.0.0.0 &
VITE_PID=$!

echo ""
echo "Open http://localhost:5173 in your browser."
echo "Press Ctrl+C to stop both servers."
echo ""

wait
