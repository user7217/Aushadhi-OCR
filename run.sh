#!/usr/bin/env bash
set -euo pipefail

# Config
API_KEY="${ROBOFLOW_API_KEY:-7tSuF7zqGS4Z9IjJpltA}"
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="${PORT:-8000}"

# Resolve repo root (where backend/ and frontend/ live)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "[1/5] Environment"
export ROBOFLOW_API_KEY="$API_KEY"
export INFERENCE_API_URL="https://infer.roboflow.com"
export DETECT_MODEL_ID=""
export ALLOW_CORS="true"
export CORS_ORIGINS="http://localhost:5173"
export PYTHONPATH="$ROOT"

echo "[2/5] Backend deps (global pip)"
if ! python3 -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  pip3 install --upgrade pip
  pip3 install -r backend/requirements.txt
fi

echo "[3/5] Frontend deps and build"
if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm not found in PATH"; exit 1
fi
pushd frontend >/dev/null
if [ ! -d node_modules ]; then
  npm install
fi
npm run build
popd >/dev/null

# Start backend server; serve built frontend via StaticFiles
echo "[4/5] Starting FastAPI on http://localhost:${BACKEND_PORT}"
cleanup() {
  echo "Stopping servers..."
  kill $UVICORN_PID >/dev/null 2>&1 || true
}
trap cleanup INT TERM

# If uvicorn not on PATH, run via python -m (more robust on macOS) [web:159][web:136]
if command -v uvicorn >/dev/null 2>&1; then
  uvicorn backend.app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload &
else
  python3 -m uvicorn backend.app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload &
fi
UVICORN_PID=$!

sleep 2
echo "[5/5] Open http://localhost:${BACKEND_PORT} (UI) or http://localhost:${BACKEND_PORT}/docs (API docs). Press Ctrl+C to stop."

wait $UVICORN_PID
