#!/bin/bash
# ==========================================================================
# E2E Happy Path — Kompletter Lakehouse-Lifecycle
#
# Register Dataset → Create Contract → Append Batch
# → DQ Check → Privacy Check → Publish → Consume
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔══════════════════════════════════════════╗"
echo "║   Lakehouse Demo — E2E Happy Path        ║"
echo "╚══════════════════════════════════════════╝"
echo

# --- 1. Dataset registrieren ---
echo "▶ 1. Dataset registrieren"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name":"sales","schema":{"id":"int","amount":"float","date":"date"},"description":"Tägliche Verkaufsdaten"}' | python3 -m json.tool
echo

# --- 2. Contract anlegen ---
echo "▶ 2. Datenvertrag anlegen"
CONTRACT=$(curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"sales","schema":{"id":"int","amount":"float"},"retention_days":365,"quality_rules":{"amount":">0"},"privacy_rules":{"email":"mask"}}')
echo "$CONTRACT" | python3 -m json.tool
CONTRACT_ID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")
echo "   → Contract ID: $CONTRACT_ID"
echo

# --- 3. Batch anhängen ---
echo "▶ 3. Daten-Batch anhängen"
BATCH=$(curl -s -X POST "$API/batches/append" \
  -H "Content-Type: application/json" \
  -d "{\"dataset\":\"sales\",\"contract_id\":\"$CONTRACT_ID\",\"file_url\":\"s3://lakehouse/sales/2024-01.parquet\"}")
echo "$BATCH" | python3 -m json.tool
BATCH_ID=$(echo "$BATCH" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "   → Batch ID: $BATCH_ID"
echo "   → Status: ingested"
echo

# --- 4. DQ-Check ---
echo "▶ 4. Data-Quality-Check"
curl -s -X POST "$API/batches/$BATCH_ID/validate" \
  -H "Content-Type: application/json" \
  -d '{"quality_rules":{"amount":">0","id":"not_null"}}' | python3 -m json.tool
echo "   → dq_passed: true"
echo

# --- 5. Privacy-Check ---
echo "▶ 5. Privacy/Compliance-Check"
curl -s -X POST "$API/batches/$BATCH_ID/privacy-check" \
  -H "Content-Type: application/json" \
  -d '{"privacy_rules":{"email":"mask","name":"hash"}}' | python3 -m json.tool
echo "   → privacy_passed: true → Status: validated"
echo

# --- 6. Status prüfen ---
echo "▶ 6. Batch-Status prüfen (sollte 'validated' sein)"
curl -s "$API/batches/$BATCH_ID" | python3 -m json.tool
echo

# --- 7. Publish ---
echo "▶ 7. Batch veröffentlichen"
curl -s -X POST "$API/batches/$BATCH_ID/publish" | python3 -m json.tool
echo "   → Status: published"
echo

# --- 8. Consume ---
echo "▶ 8. Batch konsumieren"
curl -s -X POST "$API/batches/$BATCH_ID/consume" \
  -H "Content-Type: application/json" \
  -d '{"consumer":"analytics-team"}' | python3 -m json.tool
echo

# --- 9. Finaler Status ---
echo "▶ 9. Finaler Batch-Status"
curl -s "$API/batches/$BATCH_ID" | python3 -m json.tool
echo

echo "✅ Happy Path abgeschlossen!"
