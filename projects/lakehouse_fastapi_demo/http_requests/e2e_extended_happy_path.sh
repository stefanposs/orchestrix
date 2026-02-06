#!/bin/bash
# ==========================================================================
# E2E Happy Path — EXTENDED mit SLA, Executor & Pipeline
#
# Kompletter Lakehouse-Lifecycle inkl. neuer Features:
# - Dataset & Contract mit SLA-Definition
# - Executor-Jobs für Validierung & Anonymisierung
# - Pipeline-Endpunkt für One-Shot Lifecycle
# - Dashboard-Monitoring
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   Lakehouse Demo — EXTENDED E2E Happy Path                        ║"
echo "║   Features: SLA, Executor, Pipeline, Dashboard                    ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo

# --- 1. Dataset registrieren ---
echo "▶ 1. Dataset registrieren"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name":"sales","schema":{"id":"int","amount":"float","date":"date"},"description":"Tägliche Verkaufsdaten"}' | python3 -m json.tool
echo

# --- 2. SLA definieren ---
echo "▶ 2. SLA für Dataset definieren (Freshness: 24h, Availability: 99.9%)"
SLA=$(curl -s -X POST "$API/slas" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"sales","freshness_hours":24,"availability_percent":99.9}')
echo "$SLA" | python3 -m json.tool
SLA_ID=$(echo "$SLA" | python3 -c "import sys,json;print(json.load(sys.stdin)['sla_id'])")
echo "   → SLA ID: $SLA_ID"
echo

# --- 3. Contract anlegen ---
echo "▶ 3. Datenvertrag anlegen"
CONTRACT=$(curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"sales","schema":{"id":"int","amount":"float"},"retention_days":365,"quality_rules":{"amount":">0"},"privacy_rules":{"email":"mask"}}')
echo "$CONTRACT" | python3 -m json.tool
CONTRACT_ID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")
echo "   → Contract ID: $CONTRACT_ID"
echo

# --- 4. Contract approven ---
echo "▶ 4. Contract genehmigen"
curl -s -X POST "$API/contracts/$CONTRACT_ID/approve" | python3 -m json.tool
echo

# --- 5. Batch anhängen ---
echo "▶ 5. Daten-Batch anhängen"
BATCH=$(curl -s -X POST "$API/batches/append" \
  -H "Content-Type: application/json" \
  -d "{\"dataset\":\"sales\",\"contract_id\":\"$CONTRACT_ID\",\"file_url\":\"s3://lakehouse/sales/2024-01.parquet\"}")
echo "$BATCH" | python3 -m json.tool
BATCH_ID=$(echo "$BATCH" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "   → Batch ID: $BATCH_ID"
echo "   → Status: ingested"
echo

# --- 6. Executor-Job: Validation ---
echo "▶ 6. Executor-Job: Validation (BigQuery Backend)"
EXEC_JOB=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{\"job_type\":\"validation\",\"batch_id\":\"$BATCH_ID\",\"backend\":\"bigquery\",\"params\":{\"quality_rules\":{\"amount\":\">0\"}}}")
echo "$EXEC_JOB" | python3 -m json.tool
EXEC_JOB_ID=$(echo "$EXEC_JOB" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Executor Job ID: $EXEC_JOB_ID"
echo

# --- 7. DQ-Check (manuell) ---
echo "▶ 7. Data-Quality-Check"
curl -s -X POST "$API/batches/$BATCH_ID/validate" \
  -H "Content-Type: application/json" \
  -d '{"quality_rules":{"amount":">0","id":"not_null"}}' | python3 -m json.tool
echo "   → dq_passed: true"
echo

# --- 8. Privacy-Check ---
echo "▶ 8. Privacy/Compliance-Check"
curl -s -X POST "$API/batches/$BATCH_ID/privacy-check" \
  -H "Content-Type: application/json" \
  -d '{"privacy_rules":{"email":"mask","name":"hash"}}' | python3 -m json.tool
echo "   → privacy_passed: true → Status: validated"
echo

# --- 9. SLA-Check ---
echo "▶ 9. SLA-Check durchführen"
curl -s -X POST "$API/slas/$SLA_ID/check" | python3 -m json.tool
echo

# --- 10. Publish ---
echo "▶ 10. Batch veröffentlichen"
curl -s -X POST "$API/batches/$BATCH_ID/publish" | python3 -m json.tool
echo "   → Status: published"
echo

# --- 11. Consume ---
echo "▶ 11. Batch konsumieren"
curl -s -X POST "$API/batches/$BATCH_ID/consume" \
  -H "Content-Type: application/json" \
  -d '{"consumer":"analytics-team"}' | python3 -m json.tool
echo

# --- 12. Dashboard abrufen ---
echo "▶ 12. Platform-Dashboard abrufen (Metriken, SLA-Status)"
curl -s "$API/dashboard" | python3 -m json.tool
echo

# --- 13. Pipeline-Endpunkt (One-Shot für neuen Batch) ---
echo "▶ 13. Pipeline-Job: Kompletter Lifecycle in einem Call (Ingest → Validate → Privacy → Publish)"
PIPELINE=$(curl -s -X POST "$API/pipeline/run" \
  -H "Content-Type: application/json" \
  -d "{\"dataset\":\"sales\",\"contract_id\":\"$CONTRACT_ID\",\"file_url\":\"s3://lakehouse/sales/2024-02.parquet\"}")
echo "$PIPELINE" | python3 -m json.tool
PIPELINE_BATCH_ID=$(echo "$PIPELINE" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "   → Pipeline Batch ID: $PIPELINE_BATCH_ID"
echo "   → Status: published (direkt nach Pipeline-Durchlauf)"
echo

# --- 14. Executor-Job Status prüfen ---
echo "▶ 14. Executor-Job Status prüfen"
curl -s "$API/executor/jobs/$EXEC_JOB_ID" | python3 -m json.tool
echo

# --- 15. Alle Events abrufen (Event Log) ---
echo "▶ 15. Event-Log abrufen (alle Events)"
curl -s "$API/events?limit=10" | python3 -m json.tool
echo

echo "✅ EXTENDED Happy Path abgeschlossen!"
echo "   - Dataset, Contract, SLA definiert"
echo "   - Batch ingested, validated, privacy-checked, published"
echo "   - Executor-Job für Validation ausgeführt"
echo "   - SLA-Check durchgeführt"
echo "   - Pipeline-Job für One-Shot Lifecycle genutzt"
echo "   - Dashboard-Metriken abgerufen"
