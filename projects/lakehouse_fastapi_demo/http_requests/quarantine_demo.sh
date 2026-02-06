#!/bin/bash
# ==========================================================================
# Quarantine Demo — Batch isolieren und wieder freigeben
#
# Szenario: DQ-Check findet Fehler → Quarantäne → Review → Release
#           → erneuter DQ-Check → Publish
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔══════════════════════════════════════════╗"
echo "║   Lakehouse Demo — Quarantine Workflow    ║"
echo "╚══════════════════════════════════════════╝"
echo

# --- Setup: Dataset + Contract ---
echo "▶ Setup: Dataset + Contract"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name":"orders","schema":{"order_id":"int","total":"float"},"description":"E-Commerce Bestellungen"}' | python3 -m json.tool

CONTRACT=$(curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"orders","schema":{"order_id":"int","total":"float"}}')
CONTRACT_ID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")
echo "   → Contract: $CONTRACT_ID"
echo

# --- 1. Batch anhängen ---
echo "▶ 1. Batch mit fehlerhaften Daten anhängen"
BATCH=$(curl -s -X POST "$API/batches/append" \
  -H "Content-Type: application/json" \
  -d "{\"dataset\":\"orders\",\"contract_id\":\"$CONTRACT_ID\",\"file_url\":\"s3://lakehouse/orders/bad_data.csv\"}")
BATCH_ID=$(echo "$BATCH" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "   → Batch: $BATCH_ID (status: ingested)"
echo

# --- 2. Quarantine ---
echo "▶ 2. Batch in Quarantäne setzen (Fehlerhafte Daten entdeckt!)"
curl -s -X POST "$API/batches/$BATCH_ID/quarantine" \
  -H "Content-Type: application/json" \
  -d '{"reason":"NULL-Werte in order_id Spalte — 15% der Zeilen betroffen"}' | python3 -m json.tool
echo

echo "▶ 3. Status prüfen (sollte 'quarantined' sein)"
curl -s "$API/batches/$BATCH_ID" | python3 -m json.tool
echo

# --- 3. Publish-Versuch (muss fehlschlagen!) ---
echo "▶ 4. Publish-Versuch auf quarantined Batch (Fehler erwartet!)"
curl -s -X POST "$API/batches/$BATCH_ID/publish" | python3 -m json.tool
echo "   → ⛔ Erwarteter Fehler: 'Cannot publish a quarantined batch'"
echo

# --- 4. Release ---
echo "▶ 5. Quarantäne aufheben (nach manuellem Review)"
curl -s -X POST "$API/batches/$BATCH_ID/release" | python3 -m json.tool
echo

echo "▶ 6. Status prüfen (sollte wieder 'ingested' sein)"
curl -s "$API/batches/$BATCH_ID" | python3 -m json.tool
echo

# --- 5. Jetzt normal validieren + publishen ---
echo "▶ 7. DQ-Check (diesmal bestanden)"
curl -s -X POST "$API/batches/$BATCH_ID/validate" \
  -H "Content-Type: application/json" \
  -d '{"quality_rules":{"order_id":"not_null","total":">0"}}' | python3 -m json.tool

echo
echo "▶ 8. Privacy-Check"
curl -s -X POST "$API/batches/$BATCH_ID/privacy-check" \
  -H "Content-Type: application/json" \
  -d '{"privacy_rules":{"customer_email":"mask"}}' | python3 -m json.tool

echo
echo "▶ 9. Publish (jetzt erfolgreich)"
curl -s -X POST "$API/batches/$BATCH_ID/publish" | python3 -m json.tool

echo
echo "▶ 10. Finaler Status"
curl -s "$API/batches/$BATCH_ID" | python3 -m json.tool
echo

echo "✅ Quarantine-Workflow abgeschlossen!"
