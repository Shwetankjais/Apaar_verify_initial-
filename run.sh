#!/usr/bin/env bash
set -e

# Directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting APAAR Verify by Sutrāyukti (SIH 2026 PS-26263) "
echo "=========================================================="

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Ensure storage directory exists
mkdir -p storage/documents

# Kill any lingering instances on ports 8001 or 8501
echo "Checking existing ports..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Seed baseline database if not initialized
if [ ! -f "apaar_verify.db" ]; then
    echo "Seeding baseline demo database..."
    ./venv/bin/python scripts/seed_demo.py
fi

echo "1. Starting FastAPI Backend on http://127.0.0.1:8001..."
./venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 &
BACKEND_PID=$!

sleep 2

echo "2. Starting Streamlit Frontend on http://127.0.0.1:8501..."
export API_BASE_URL="http://127.0.0.1:8001"
./venv/bin/streamlit run frontend/app.py --server.port 8501 --server.headless true &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo " 🎉 APAAR Verify Platform is running locally:"
echo " • Frontend Web UI:  http://localhost:8501"
echo " • Backend REST API: http://localhost:8001"
echo " • Swagger Docs:     http://localhost:8001/docs"
echo "=========================================================="
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit" INT TERM
wait

