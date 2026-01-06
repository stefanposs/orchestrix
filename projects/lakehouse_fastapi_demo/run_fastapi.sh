#!/usr/bin/env bash
set -e

# --------------------------------------
# Configuration (static defaults)
# Kann über Environment-Variablen überschrieben werden
# --------------------------------------

echo "Starting FastAPI Base..."

# Host / Port / Environment
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
ENV="${ENV:-dev}"

echo "Starting FastAPI Base..."
echo "HOST: $HOST"
echo "PORT: $PORT"
echo "ENV: $ENV"

# Set working directory to repo root and PYTHONPATH to use local code
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$SCRIPT_DIR/../.."
export PYTHONPATH="$REPO_ROOT/bases:$PYTHONPATH"
cd "$REPO_ROOT"
echo "Python Module: bases.orchestrix.lakehouse_fastapi_demo.app:app (local code)"

# --------------------------------------
# Run uvicorn
# --------------------------------------
if [ "$ENV" == "prod" ]; then
    uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --host $HOST --port $PORT
else
    uv run uvicorn bases.orchestrix.lakehouse_fastapi_demo.app:app --host $HOST --port $PORT --reload
fi