#!/usr/bin/env bash
# Dev mode: run API server (requires Linux/WSL + make dist + assets/starter.ini)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f "$ROOT/dist/libbackend.so" ]; then
  echo "Building C backend..."
  make dist
fi

if [ ! -f "$ROOT/assets/starter.ini" ]; then
  echo "ERROR: assets/starter.ini not found."
  echo "Copy your course world config to assets/starter.ini"
  exit 1
fi

export LD_LIBRARY_PATH="$ROOT/dist:${LD_LIBRARY_PATH:-}"

cd "$ROOT/python"
python3 -m pip install -q --break-system-packages -r requirements-web.txt 2>/dev/null \
  || python3 -m pip install -q -r requirements-web.txt

echo "API server -> http://localhost:8000"
echo "In another terminal: cd web && npm run dev"
python3 run_server.py --host 0.0.0.0 --port 8000 --config "$ROOT/assets/starter.ini"
