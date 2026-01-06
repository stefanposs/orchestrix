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
echo "Python Module: orchestrix.lakehouse_fastapi_demo.app:app"

# --------------------------------------
# Run uvicorn
# --------------------------------------
if [ "$ENV" == "prod" ]; then
    uv run uvicorn orchestrix.lakehouse_fastapi_demo.app:app --host $HOST --port $PORT
else
    uv run uvicorn orchestrix.lakehouse_fastapi_demo.app:app --host $HOST --port $PORT --reload
fi