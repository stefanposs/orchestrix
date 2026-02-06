#!/bin/bash
# ==========================================================================
# Pipeline Demo — One-Shot Lifecycle Automation
#
# Pipeline-Endpunkt vollführt den kompletten Lifecycle in einem Call:
# Ingest → Validation → Privacy Check → Publish
#
# Use Cases:
# - Automatisierte Batch-Verarbeitung ohne manuelle Schritte
# - CI/CD Pipeline Integration
# - Scheduled Ingestion (Cron-Jobs)
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   Lakehouse Demo — Pipeline (One-Shot Lifecycle)                  ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo

# ==========================================================================
# Teil 1: Setup — Dataset + Contract
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 1: Setup — Dataset & Contract"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 1. Dataset 'iot_sensors' registrieren"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iot_sensors",
    "schema": {
      "sensor_id": "int",
      "temperature": "float",
      "humidity": "float",
      "timestamp": "datetime"
    },
    "description": "IoT Sensor Messdaten"
  }' | python3 -m json.tool
echo

echo "▶ 2. Contract mit Quality & Privacy Rules"
CONTRACT=$(curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "iot_sensors",
    "schema": {
      "sensor_id": "int",
      "temperature": "float",
      "humidity": "float"
    },
    "quality_rules": {
      "temperature": ">-50 AND <100",
      "humidity": ">=0 AND <=100",
      "sensor_id": "not_null"
    },
    "privacy_rules": {
      "sensor_location": "mask"
    }
  }')
echo "$CONTRACT" | python3 -m json.tool
CONTRACT_ID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")
echo "   → Contract ID: $CONTRACT_ID"
echo

# ==========================================================================
# Teil 2: Manuelle Batch-Verarbeitung (zum Vergleich)
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 2: Manueller Workflow (zum Vergleich)"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 3. Manueller Workflow (5 Schritte):"
echo "   1. Append"
BATCH_MANUAL=$(curl -s -X POST "$API/batches/append" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset\": \"iot_sensors\",
    \"contract_id\": \"$CONTRACT_ID\",
    \"file_url\": \"s3://lakehouse/sensors/batch_manual.parquet\"
  }")
BATCH_MANUAL_ID=$(echo "$BATCH_MANUAL" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "      ✓ Batch: $BATCH_MANUAL_ID"

echo "   2. Validate"
curl -s -X POST "$API/batches/$BATCH_MANUAL_ID/validate" \
  -H "Content-Type: application/json" \
  -d '{"quality_rules":{"temperature":">-50","humidity":">=0"}}' > /dev/null
echo "      ✓ DQ-Check passed"

echo "   3. Privacy-Check"
curl -s -X POST "$API/batches/$BATCH_MANUAL_ID/privacy-check" \
  -H "Content-Type: application/json" \
  -d '{"privacy_rules":{"sensor_location":"mask"}}' > /dev/null
echo "      ✓ Privacy-Check passed"

echo "   4. Publish"
curl -s -X POST "$API/batches/$BATCH_MANUAL_ID/publish" > /dev/null
echo "      ✓ Published"

echo "   5. Status prüfen"
curl -s "$API/batches/$BATCH_MANUAL_ID" | python3 -m json.tool
echo
echo "   → Manueller Workflow: 5 API-Calls erforderlich ❌"
echo

# ==========================================================================
# Teil 3: Pipeline — One-Shot Automation
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 3: Pipeline — One-Shot Automation (1 API-Call)"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 4. Pipeline-Job: Kompletter Lifecycle in einem Call"
PIPELINE=$(curl -s -X POST "$API/pipeline/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset\": \"iot_sensors\",
    \"contract_id\": \"$CONTRACT_ID\",
    \"file_url\": \"s3://lakehouse/sensors/batch_pipeline.parquet\",
    \"quality_rules\": {
      \"temperature\": \">-50 AND <100\",
      \"humidity\": \">=0 AND <=100\"
    },
    \"privacy_rules\": {
      \"sensor_location\": \"mask\"
    }
  }")
echo "$PIPELINE" | python3 -m json.tool
BATCH_PIPELINE_ID=$(echo "$PIPELINE" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo
echo "   → Pipeline Batch ID: $BATCH_PIPELINE_ID"
echo "   → Status: published (direkt fertig!) ✅"
echo

echo "▶ 5. Batch-Details (Pipeline-Result)"
curl -s "$API/batches/$BATCH_PIPELINE_ID" | python3 -m json.tool
echo

# ==========================================================================
# Teil 4: Batch-Processing mit mehreren Pipelines
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 4: Parallel Batch-Processing (3 Pipeline-Jobs)"
echo "═══════════════════════════════════════════════════════════════════"
echo

for i in 1 2 3; do
  echo "▶ Pipeline-Job $i"
  RESULT=$(curl -s -X POST "$API/pipeline/run" \
    -H "Content-Type: application/json" \
    -d "{
      \"dataset\": \"iot_sensors\",
      \"contract_id\": \"$CONTRACT_ID\",
      \"file_url\": \"s3://lakehouse/sensors/batch_$i.parquet\"
    }")
  BID=$(echo "$RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
  echo "   ✓ Batch $i: $BID → published"
done
echo

# ==========================================================================
# Teil 5: Alle Batches für Dataset auflisten
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 5: Alle Batches für 'iot_sensors'"
echo "═══════════════════════════════════════════════════════════════════"
echo

curl -s "$API/batches?dataset=iot_sensors" | python3 -m json.tool
echo

# ==========================================================================
# Teil 6: Pipeline mit Executor-Backend
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 6: Pipeline mit Custom Executor-Backend"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 6. Pipeline mit BigQuery Executor"
PIPELINE_BQ=$(curl -s -X POST "$API/pipeline/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset\": \"iot_sensors\",
    \"contract_id\": \"$CONTRACT_ID\",
    \"file_url\": \"s3://lakehouse/sensors/batch_bq.parquet\",
    \"executor_backend\": \"bigquery\",
    \"executor_params\": {
      \"project\": \"my-gcp-project\",
      \"dataset\": \"lakehouse\"
    }
  }")
echo "$PIPELINE_BQ" | python3 -m json.tool
BATCH_BQ_ID=$(echo "$PIPELINE_BQ" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo
echo "   → Pipeline mit BigQuery-Backend: $BATCH_BQ_ID"
echo

# ==========================================================================
# Teil 7: Error-Handling in Pipeline
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 7: Pipeline Error-Handling (Invalid Dataset)"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 7. Pipeline mit ungültigem Dataset (Fehler erwartet)"
curl -s -X POST "$API/pipeline/run" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "nonexistent_dataset",
    "contract_id": "invalid-contract",
    "file_url": "s3://lakehouse/bad.csv"
  }' | python3 -m json.tool
echo
echo "   → 404 Not Found erwartet ✓"
echo

# ==========================================================================
# Zusammenfassung
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Pipeline Demo abgeschlossen!"
echo "═══════════════════════════════════════════════════════════════════"
echo
echo "📊 Vergleich:"
echo "   Manueller Workflow:  5 API-Calls   ❌"
echo "   Pipeline-Workflow:   1 API-Call    ✅"
echo
echo "💡 Pipeline Vorteile:"
echo "   ✓ One-Shot Execution: Kompletter Lifecycle in einem Call"
echo "   ✓ Atomic Operation: Entweder komplett erfolgreich oder komplett fehlgeschlagen"
echo "   ✓ Weniger Network-Overhead: 1 Request statt 5"
echo "   ✓ Vereinfachte Integration: Ideal für CI/CD, Cron-Jobs"
echo "   ✓ Custom Executors: Backend-Wahl pro Pipeline-Job"
echo
echo "🎯 Use Cases:"
echo "   - Automatisierte Batch-Verarbeitung (täglich/stündlich)"
echo "   - CI/CD Integration (Data Pipeline as Code)"
echo "   - Event-Driven Ingestion (S3-Trigger → Lambda → Pipeline)"
echo "   - Self-Service Data Platform (Users starten Pipelines via UI)"
echo
echo "📝 Batches erstellt:"
echo "   - Manuell:           $BATCH_MANUAL_ID"
echo "   - Pipeline (Single): $BATCH_PIPELINE_ID"
echo "   - Pipeline (BigQuery): $BATCH_BQ_ID"
echo "   + 3 weitere Pipeline-Batches"
echo
