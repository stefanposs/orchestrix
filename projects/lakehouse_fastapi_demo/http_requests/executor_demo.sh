#!/bin/bash
# ==========================================================================
# Executor Demo — Pluggable Multi-Backend Job Execution
#
# Shows how the Executor-Layer executes different job types on various backends:
# - Local Python: Fast, in-process validation
# - BigQuery: Cloud-native, scalable validation
# - Spark: Distributed processing for large batches
# - dbt: Transformations and data quality rules
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   Lakehouse Demo — Executor Layer (Multi-Backend Jobs)            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo

# --- Setup: Dataset + Contract + Batch ---
echo "▶ Setup: Dataset, Contract, Batch"
curl -s -X POST "$API/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name":"transactions","schema":{"tx_id":"int","amount":"float","user_id":"int","timestamp":"datetime"},"description":"Payment Transactions"}' > /dev/null

CONTRACT=$(curl -s -X POST "$API/contracts" \
  -H "Content-Type: application/json" \
  -d '{"dataset":"transactions","schema":{"tx_id":"int","amount":"float"},"quality_rules":{"amount":">0","tx_id":"not_null"},"privacy_rules":{"user_id":"hash"}}')
CONTRACT_ID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")

BATCH=$(curl -s -X POST "$API/batches/append" \
  -H "Content-Type: application/json" \
  -d "{\"dataset\":\"transactions\",\"contract_id\":\"$CONTRACT_ID\",\"file_url\":\"s3://lakehouse/transactions/2024-01.parquet\"}")
BATCH_ID=$(echo "$BATCH" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
echo "   ✓ Dataset: transactions"
echo "   ✓ Contract: $CONTRACT_ID"
echo "   ✓ Batch: $BATCH_ID"
echo

# ==========================================================================
# Part 1: Available Backends
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "PART 1: Available Executor Backends"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 1. List all available backends"
curl -s "$API/executor/backends" | python3 -m json.tool
echo
echo "   Supported Backends:"
echo "   - local_python: In-process Python execution (fast, local)"
echo "   - bigquery: Google BigQuery (Cloud, scalable)"
echo "   - spark: Apache Spark (Distributed processing)"
echo "   - dbt: Data Build Tool (Transformations, DQ)"
echo

# ==========================================================================
# Part 2: Validation Jobs on different backends
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "PART 2: Validation Jobs on different backends"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 2a. Validation Job: Local Python Backend"
echo "   Use Case: Fast validation for small batches (<100MB)"
JOB_LOCAL=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"validation\",
    \"batch_id\": \"$BATCH_ID\",
    \"backend\": \"local_python\",
    \"params\": {
      \"quality_rules\": {\"amount\": \">0\", \"tx_id\": \"not_null\"}
    }
  }")
echo "$JOB_LOCAL" | python3 -m json.tool
JOB_LOCAL_ID=$(echo "$JOB_LOCAL" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Job ID: $JOB_LOCAL_ID"
echo

echo "▶ 2b. Validation Job: BigQuery Backend"
echo "   Use Case: Cloud-native validation, scalable up to TB"
JOB_BQ=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"validation\",
    \"batch_id\": \"$BATCH_ID\",
    \"backend\": \"bigquery\",
    \"params\": {
      \"quality_rules\": {\"amount\": \">0\"},
      \"project\": \"my-gcp-project\",
      \"dataset\": \"lakehouse\"
    }
  }")
echo "$JOB_BQ" | python3 -m json.tool
JOB_BQ_ID=$(echo "$JOB_BQ" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Job ID: $JOB_BQ_ID"
echo

echo "▶ 2c. Validation Job: Spark Backend"
echo "   Use Case: Distributed processing for large batches (>1GB)"
JOB_SPARK=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"validation\",
    \"batch_id\": \"$BATCH_ID\",
    \"backend\": \"spark\",
    \"params\": {
      \"quality_rules\": {\"amount\": \">0\"},
      \"cluster\": \"prod-cluster\",
      \"partitions\": 100
    }
  }")
echo "$JOB_SPARK" | python3 -m json.tool
JOB_SPARK_ID=$(echo "$JOB_SPARK" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Job ID: $JOB_SPARK_ID"
echo

# ==========================================================================
# Teil 3: Anonymization Jobs
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 3: Anonymization Jobs (PII-Protection)"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 3a. Anonymization Job: Local Python"
echo "   Use Case: Quick masking/hashing für Development/Testing"
JOB_ANON=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"anonymization\",
    \"batch_id\": \"$BATCH_ID\",
    \"backend\": \"local_python\",
    \"params\": {
      \"privacy_rules\": {\"user_id\": \"hash\", \"email\": \"mask\"}
    }
  }")
echo "$JOB_ANON" | python3 -m json.tool
JOB_ANON_ID=$(echo "$JOB_ANON" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Job ID: $JOB_ANON_ID"
echo

echo "▶ 3b. Anonymization Job: dbt Backend"
echo "   Use Case: Komplexe Transforms mit SQL-based privacy rules"
JOB_DBT=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"anonymization\",
    \"batch_id\": \"$BATCH_ID\",
    \"backend\": \"dbt\",
    \"params\": {
      \"model\": \"privacy_transform\",
      \"target\": \"prod\"
    }
  }")
echo "$JOB_DBT" | python3 -m json.tool
JOB_DBT_ID=$(echo "$JOB_DBT" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Job ID: $JOB_DBT_ID"
echo

# ==========================================================================
# Teil 4: Publish Jobs (High-Throughput)
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 4: Publish Jobs (Optimierte File-Formate)"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 4. Publish Job: Spark Backend"
echo "   Use Case: Konvertierung zu Parquet/ORC, Partitionierung, Indexing"
JOB_PUBLISH=$(curl -s -X POST "$API/executor/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"publish\",
    \"batch_id\": \"$BATCH_ID\",
    \"backend\": \"spark\",
    \"params\": {
      \"output_format\": \"parquet\",
      \"partition_by\": [\"date\"],
      \"compression\": \"snappy\"
    }
  }")
echo "$JOB_PUBLISH" | python3 -m json.tool
JOB_PUBLISH_ID=$(echo "$JOB_PUBLISH" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "   → Job ID: $JOB_PUBLISH_ID"
echo

# ==========================================================================
# Teil 5: Job-Status überwachen
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 5: Job-Status überwachen"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 5a. Status: Local Python Validation"
curl -s "$API/executor/jobs/$JOB_LOCAL_ID" | python3 -m json.tool
echo

echo "▶ 5b. Status: BigQuery Validation"
curl -s "$API/executor/jobs/$JOB_BQ_ID" | python3 -m json.tool
echo

echo "▶ 5c. Status: Spark Validation"
curl -s "$API/executor/jobs/$JOB_SPARK_ID" | python3 -m json.tool
echo

# ==========================================================================
# Teil 6: Alle Jobs für einen Batch auflisten
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 6: Alle Jobs für Batch '$BATCH_ID'"
echo "═══════════════════════════════════════════════════════════════════"
echo
curl -s "$API/executor/jobs?batch_id=$BATCH_ID" | python3 -m json.tool
echo

# ==========================================================================
# Zusammenfassung
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Executor Demo abgeschlossen!"
echo "═══════════════════════════════════════════════════════════════════"
echo
echo "📊 Jobs erstellt:"
echo "   - Local Python Validation:  $JOB_LOCAL_ID"
echo "   - BigQuery Validation:      $JOB_BQ_ID"
echo "   - Spark Validation:         $JOB_SPARK_ID"
echo "   - Local Python Anonymize:   $JOB_ANON_ID"
echo "   - dbt Anonymize:            $JOB_DBT_ID"
echo "   - Spark Publish:            $JOB_PUBLISH_ID"
echo
echo "💡 Wichtige Konzepte:"
echo "   ✓ Job-Typen: validation, anonymization, publish"
echo "   ✓ Backends: local_python, bigquery, spark, dbt"
echo "   ✓ Pluggable Architektur: Backend-agnostisch"
echo "   ✓ Async Execution: Jobs laufen parallel, Status-Polling"
echo
echo "🎯 Use Cases:"
echo "   - Local Python:  Development, Testing, kleine Batches"
echo "   - BigQuery:      Cloud-native, serverless Processing"
echo "   - Spark:         Distributed, große Batches (>1GB)"
echo "   - dbt:           SQL-based Transforms + DQ Rules"
echo
