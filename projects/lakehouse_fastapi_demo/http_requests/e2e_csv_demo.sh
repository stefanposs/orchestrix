#!/bin/bash
# End-to-End Demo: Register, upload CSV, download CSV (signed URLs)
set -e
API_URL="http://localhost:8000"

# 1. Register dataset
echo "Registering dataset..."
curl -s -X POST "$API_URL/datasets" -H "Content-Type: application/json" -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}}' | jq

echo
# 2. Register contract
echo "Registering contract..."
curl -s -X POST "$API_URL/contracts" -H "Content-Type: application/json" -d '{"dataset": "sales", "retention_days": 30}' | jq

echo
# 3. Get signed upload URL for CSV
echo "Getting signed upload URL..."
UPLOAD_URL=$(curl -s -X POST "$API_URL/datasets/sales/upload-url" -H "Content-Type: application/json" -d '{"filename": "sales_2024_01.csv"}' | jq -r .url)
echo "Upload URL: $UPLOAD_URL"

echo
# 4. Upload CSV file to signed URL
echo "Uploading CSV file..."
curl -s -X PUT "$UPLOAD_URL" -H "Content-Type: text/csv" --upload-file sales_2024_01.csv

echo
# 5. (Optional) Replay events
echo "Replaying events..."
curl -s -X POST "$API_URL/replay" -H "Content-Type: application/json" -d '{"dataset": "sales"}' | jq

echo
# 6. Get signed download URL for CSV
echo "Getting signed download URL..."
DOWNLOAD_URL=$(curl -s -X POST "$API_URL/datasets/sales/download-url" -H "Content-Type: application/json" -d '{"filename": "sales_2024_01.csv"}' | jq -r .url)
echo "Download URL: $DOWNLOAD_URL"

echo
# 7. Download CSV file from signed URL
echo "Downloading CSV file..."
curl -s -L "$DOWNLOAD_URL" -o downloaded_sales.csv
echo "Downloaded file: downloaded_sales.csv"
