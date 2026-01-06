#!/bin/bash
# Szenario: Konsumieren aller vorhandenen Batches (CSV-Dateien)
set -e
API_URL="http://localhost:8000"

# Liste der bekannten Batches (Dateinamen)
BATCHES=("sales_2024_01.csv" "sales_2024_02.csv")

for BATCH in "${BATCHES[@]}"; do
  echo "Getting signed download URL for $BATCH..."
  DOWNLOAD_URL=$(curl -s -X POST "$API_URL/datasets/sales/download-url" -H "Content-Type: application/json" -d '{"filename": "'$BATCH'"}' | jq -r .url)
  echo "Download URL: $DOWNLOAD_URL"
  curl -s -L "$DOWNLOAD_URL" -o "downloaded_$BATCH"
  echo "Downloaded file: downloaded_$BATCH"
done
