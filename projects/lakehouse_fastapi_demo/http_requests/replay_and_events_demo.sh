#!/bin/bash
# ==========================================================================
# Replay & Events Demo — Event Store abfragen und Replay ausführen
#
# Szenario: Mehrere Datasets registrieren, Batches anhängen,
#           Events abfragen und Replay durchführen
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔══════════════════════════════════════════╗"
echo "║   Lakehouse Demo — Replay & Events        ║"
echo "╚══════════════════════════════════════════╝"
echo

# --- 1. Mehrere Datasets registrieren ---
echo "▶ 1. Datasets registrieren"
for DS in "inventory" "marketing"; do
  curl -s -X POST "$API/datasets" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$DS\",\"schema\":{\"id\":\"int\",\"value\":\"float\"},\"description\":\"$DS data\"}" | python3 -m json.tool
  echo
done

# --- 2. Contracts + Batches ---
echo "▶ 2. Contracts + Batches anlegen"
for DS in "inventory" "marketing"; do
  CONTRACT=$(curl -s -X POST "$API/contracts" \
    -H "Content-Type: application/json" \
    -d "{\"dataset\":\"$DS\",\"schema\":{\"id\":\"int\",\"value\":\"float\"}}")
  CID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")

  curl -s -X POST "$API/batches/append" \
    -H "Content-Type: application/json" \
    -d "{\"dataset\":\"$DS\",\"contract_id\":\"$CID\",\"file_url\":\"s3://lakehouse/$DS/batch1.parquet\"}" | python3 -m json.tool
  echo
done

# --- 3. Alle Datasets auflisten ---
echo "▶ 3. Alle Datasets"
curl -s "$API/datasets" | python3 -m json.tool
echo

# --- 4. Alle Batches auflisten ---
echo "▶ 4. Alle Batches"
curl -s "$API/batches" | python3 -m json.tool
echo

# --- 5. Replay für ein Dataset ---
echo "▶ 5. Replay: inventory"
curl -s -X POST "$API/events/replay" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"inventory"}' | python3 -m json.tool
echo

# --- 6. Event-Log abfragen (alle) ---
echo "▶ 6. Alle Events im Store"
curl -s "$API/events" | python3 -m json.tool
echo

# --- 7. Events filtern ---
echo "▶ 7. Events für dataset-inventory"
curl -s "$API/events?aggregate_id=dataset-inventory" | python3 -m json.tool
echo

echo "▶ 8. Nur DatasetRegistered Events"
curl -s "$API/events?event_type=DatasetRegistered" | python3 -m json.tool
echo

# --- 8. Health Check ---
echo "▶ 9. Health + Readiness"
curl -s "$API/health" | python3 -m json.tool
curl -s "$API/ready" | python3 -m json.tool
echo

echo "✅ Replay & Events Demo abgeschlossen!"
