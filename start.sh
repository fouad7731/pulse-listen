#!/bin/bash
# Lance backend (API FastAPI) + frontend (Next.js) en une commande.
# Usage : ./start.sh    puis ouvrir http://localhost:3000
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> Demarrage backend (API :8000)..."
cd "$ROOT/backend"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > api.log 2>&1 &
API_PID=$!
echo "    backend PID $API_PID (logs: backend/api.log)"

sleep 5

echo "==> Demarrage frontend (dashboard :3000)..."
cd "$ROOT/frontend"
npm run dev > dev.log 2>&1 &
WEB_PID=$!
echo "    frontend PID $WEB_PID (logs: frontend/dev.log)"

sleep 6

echo ""
echo "============================================="
echo "  Dashboard : http://localhost:3000"
echo "  API       : http://127.0.0.1:8000"
echo "  API docs  : http://127.0.0.1:8000/docs"
echo "============================================="
echo ""
echo "Pour tout arreter :  kill $API_PID $WEB_PID"
echo "(ou ferme ce terminal / Ctrl+C)"

# Garde le script vivant pour que Ctrl+C tue les deux serveurs
trap "echo 'Arret...'; kill $API_PID $WEB_PID 2>/dev/null; exit 0" INT TERM
wait
