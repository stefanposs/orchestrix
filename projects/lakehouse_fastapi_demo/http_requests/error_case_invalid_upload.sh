#!/bin/bash
# Szenario: Fehlerfall – ungültiger Upload (z.B. falsches Format)
set -e
API_URL="http://localhost:8000"

# 1. Get signed upload URL für ungültige Datei
echo "Getting signed upload URL for invalid batch..."
UPLOAD_URL=$(curl -s -X POST "$API_URL/datasets/sales/upload-url" -H "Content-Type: application/json" -d '{"filename": "invalid_batch.txt"}' | jq -r .url)
echo "Upload URL: $UPLOAD_URL"

echo "Create invalid file..."
echo "not,a,csv,at,all" > invalid_batch.txt

# 2. Upload invalid file
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X PUT "$UPLOAD_URL" -H "Content-Type: text/plain" --upload-file invalid_batch.txt)
echo "HTTP response code: $RESPONSE (should be 400 or 415 if validation is strict)"
