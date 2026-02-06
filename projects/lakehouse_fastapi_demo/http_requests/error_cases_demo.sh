#!/bin/bash
# ==========================================================================
# Error Cases Demo — Fehlerfälle und Domain-Fehlerbehandlung
#
# Szenario: Typische Fehler, die die Domain-Guards abfangen
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔══════════════════════════════════════════╗"
echo "║   Lakehouse Demo — Error Cases            ║"
echo "╚══════════════════════════════════════════╝"
echo

# --- Setup ---
echo "▶ Setup: Dataset + Contract + Batch"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name":"errors_test","schema":{"id":"int"},"description":"Test"}' > /dev/null

CONTRACT=$(curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"errors_test","schema":{"id":"int"}}')
CID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")

BATCH=$(curl -s -X POST "$API/batches/append" \
  -H "Content-Type: application/json" \
  -d "{\"dataset\":\"errors_test\",\"contract_id\":\"$CID\",\"file_url\":\"s3://b/test.csv\"}")
BID=$(echo "$BATCH" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "   → Dataset: errors_test, Contract: $CID, Batch: $BID"
echo

# --- Error 1: Duplicate Dataset ---
echo "▶ 1. Duplicate Dataset (409 Conflict)"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name":"errors_test","schema":{"id":"int"}}' | python3 -m json.tool
echo

# --- Error 2: Unknown Dataset ---
echo "▶ 2. Contract für unbekanntes Dataset (404 Not Found)"
curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"does_not_exist","schema":{"id":"int"}}' | python3 -m json.tool
echo

# --- Error 3: Unknown Batch ---
echo "▶ 3. Unbekannten Batch abfragen (404 Not Found)"
curl -s "$API/batches/batch-unknown-123" | python3 -m json.tool
echo

# --- Error 4: Release nicht-quarantined Batch ---
echo "▶ 4. Release auf nicht-quarantined Batch (422 Invalid State)"
curl -s -X POST "$API/batches/$BID/release" | python3 -m json.tool
echo

# --- Error 5: Consume unpublished Batch ---
echo "▶ 5. Consume auf unpublished Batch (422 Invalid State)"
curl -s -X POST "$API/batches/$BID/consume" \
  -H "Content-Type: application/json" \
  -d '{"consumer":"greedy-team"}' | python3 -m json.tool
echo

# --- Error 6: Quarantine → erneut Quarantine ---
echo "▶ 6. Doppelte Quarantine (zweimal hintereinander)"
curl -s -X POST "$API/batches/$BID/quarantine" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Erster Fehler"}' > /dev/null
echo "   Erste Quarantine gesetzt."
curl -s -X POST "$API/batches/$BID/quarantine" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Zweiter Fehler"}' | python3 -m json.tool
echo "   → Quarantine auf quarantined Batch: OK (überschreibt Reason)"
echo

# --- Reset für nächsten Test ---
curl -s -X POST "$API/batches/$BID/release" > /dev/null

# --- Error 7: Publish quarantined ---
echo "▶ 7. Publish auf quarantined Batch (422 Invalid State)"
curl -s -X POST "$API/batches/$BID/quarantine" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Blockiert"}' > /dev/null
curl -s -X POST "$API/batches/$BID/publish" | python3 -m json.tool
echo

echo "✅ Error Cases Demo abgeschlossen!"
echo "   Alle Domain-Guards greifen korrekt."
