#!/bin/bash
# Szenario: Append weitere Daten und konsumiere mehrere CSVs
set -e
API_URL="http://localhost:8000"

# 1. Register weiteres Batch (neue CSV)
echo "Getting signed upload URL for batch 2..."
UPLOAD_URL2=$(curl -s -X POST "$API_URL/datasets/sales/upload-url" -H "Content-Type: application/json" -d '{"filename": "sales_2024_02.csv"}' | jq -r .url)
echo "Upload URL: $UPLOAD_URL2"

echo "Create new CSV for batch 2..."
echo -e "id,amount\n4,400.0\n5,500.0" > sales_2024_02.csv

# 2. Upload batch 2
curl -s -X PUT "$UPLOAD_URL2" -H "Content-Type: text/csv" --upload-file sales_2024_02.csv

echo
# 3. Download batch 2
DOWNLOAD_URL2=$(curl -s -X POST "$API_URL/datasets/sales/download-url" -H "Content-Type: application/json" -d '{"filename": "sales_2024_02.csv"}' | jq -r .url)
echo "Download URL: $DOWNLOAD_URL2"
curl -s -L "$DOWNLOAD_URL2" -o downloaded_sales_02.csv
echo "Downloaded file: downloaded_sales_02.csv"
