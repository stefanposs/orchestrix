#!/bin/bash
# Szenario: Replay für mehrere Datasets
set -e
API_URL="http://localhost:8000"

DATASETS=("sales" "marketing")

for DS in "${DATASETS[@]}"; do
  echo "Registering dataset $DS..."
  curl -s -X POST "$API_URL/datasets" -H "Content-Type: application/json" -d '{"name": "'$DS'", "schema": {"id": "int", "amount": "float"}}' | jq
  echo
  echo "Registering contract for $DS..."
  curl -s -X POST "$API_URL/contracts" -H "Content-Type: application/json" -d '{"dataset": "'$DS'", "retention_days": 30}' | jq
  echo
  echo "Replaying $DS..."
  curl -s -X POST "$API_URL/replay" -H "Content-Type: application/json" -d '{"dataset": "'$DS'"}' | jq
  echo
  echo "---"
done
