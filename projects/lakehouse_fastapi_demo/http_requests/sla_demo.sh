#!/bin/bash
# ==========================================================================
# SLA Demo — Service Level Agreement Monitoring
#
# Zeigt SLA-Definition, -Monitoring und -Breach Detection:
# - Freshness SLA: Daten müssen innerhalb von X Stunden eintreffen
# - Availability SLA: Mindest-Verfügbarkeit in Prozent
# - SLA-Check: Automatische Prüfung + Breach-Detection
# - Dashboard: Aggregierte SLA-Metriken
# ==========================================================================
set -euo pipefail
API="http://localhost:8000"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   Lakehouse Demo — SLA Monitoring & Dashboard                     ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo

# ==========================================================================
# Teil 1: Setup — Datasets registrieren
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 1: Setup — Critical Datasets registrieren"
echo "═══════════════════════════════════════════════════════════════════"
echo

for DS in "orders" "payments" "shipments"; do
  echo "▶ Dataset: $DS"
  curl -s -X POST "$API/datasets" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$DS\",\"schema\":{\"id\":\"int\",\"timestamp\":\"datetime\"},\"description\":\"$DS data\"}" > /dev/null
  echo "   ✓ registriert"
done
echo

# ==========================================================================
# Teil 2: SLA-Definitionen
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 2: SLA-Definitionen für kritische Datasets"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 2a. SLA für 'orders' (Business-Critical: 99.9% Availability, 1h Freshness)"
SLA_ORDERS=$(curl -s -X POST "$API/slas" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "orders",
    "freshness_hours": 1,
    "availability_percent": 99.9
  }')
echo "$SLA_ORDERS" | python3 -m json.tool
SLA_ORDERS_ID=$(echo "$SLA_ORDERS" | python3 -c "import sys,json;print(json.load(sys.stdin)['sla_id'])")
echo "   → SLA ID: $SLA_ORDERS_ID"
echo

echo "▶ 2b. SLA für 'payments' (High-Priority: 99.5% Availability, 30min Freshness)"
SLA_PAYMENTS=$(curl -s -X POST "$API/slas" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "payments",
    "freshness_hours": 0.5,
    "availability_percent": 99.5
  }')
echo "$SLA_PAYMENTS" | python3 -m json.tool
SLA_PAYMENTS_ID=$(echo "$SLA_PAYMENTS" | python3 -c "import sys,json;print(json.load(sys.stdin)['sla_id'])")
echo "   → SLA ID: $SLA_PAYMENTS_ID"
echo

echo "▶ 2c. SLA für 'shipments' (Standard: 95% Availability, 24h Freshness)"
SLA_SHIPMENTS=$(curl -s -X POST "$API/slas" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "shipments",
    "freshness_hours": 24,
    "availability_percent": 95.0
  }')
echo "$SLA_SHIPMENTS" | python3 -m json.tool
SLA_SHIPMENTS_ID=$(echo "$SLA_SHIPMENTS" | python3 -c "import sys,json;print(json.load(sys.stdin)['sla_id'])")
echo "   → SLA ID: $SLA_SHIPMENTS_ID"
echo

# ==========================================================================
# Teil 3: Alle SLAs auflisten
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 3: Alle definierten SLAs auflisten"
echo "═══════════════════════════════════════════════════════════════════"
echo

curl -s "$API/slas" | python3 -m json.tool
echo

# ==========================================================================
# Teil 4: Contracts + Batches für SLA-Monitoring
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 4: Batches ingesten (für SLA-Freshness-Check)"
echo "═══════════════════════════════════════════════════════════════════"
echo

for DS in "orders" "payments" "shipments"; do
  CONTRACT=$(curl -s -X POST "$API/contracts" \
    -H "Content-Type: application/json" \
    -d "{\"dataset\":\"$DS\",\"schema\":{\"id\":\"int\"}}")
  CID=$(echo "$CONTRACT" | python3 -c "import sys,json;print(json.load(sys.stdin)['contract_id'])")

  echo "▶ Batch für '$DS'"
  BATCH=$(curl -s -X POST "$API/batches/append" \
    -H "Content-Type: application/json" \
    -d "{\"dataset\":\"$DS\",\"contract_id\":\"$CID\",\"file_url\":\"s3://lakehouse/$DS/batch1.parquet\"}")
  BID=$(echo "$BATCH" | python3 -c "import sys,json;print(json.load(sys.stdin)['batch_id'])")
  echo "   ✓ Batch: $BID"
  
  # DQ + Privacy Check
  curl -s -X POST "$API/batches/$BID/validate" \
    -H "Content-Type: application/json" \
    -d '{"quality_rules":{"id":"not_null"}}' > /dev/null
  curl -s -X POST "$API/batches/$BID/privacy-check" \
    -H "Content-Type: application/json" \
    -d '{"privacy_rules":{}}' > /dev/null
  
  # Publish
  curl -s -X POST "$API/batches/$BID/publish" > /dev/null
  echo "   ✓ Published"
done
echo

# ==========================================================================
# Teil 5: SLA-Checks durchführen
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 5: SLA-Checks durchführen"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 5a. SLA-Check: orders"
curl -s -X POST "$API/slas/$SLA_ORDERS_ID/check" | python3 -m json.tool
echo

echo "▶ 5b. SLA-Check: payments"
curl -s -X POST "$API/slas/$SLA_PAYMENTS_ID/check" | python3 -m json.tool
echo

echo "▶ 5c. SLA-Check: shipments"
curl -s -X POST "$API/slas/$SLA_SHIPMENTS_ID/check" | python3 -m json.tool
echo

# ==========================================================================
# Teil 6: SLA-Status abrufen
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 6: Detaillierte SLA-Status"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 6a. SLA-Details: orders"
curl -s "$API/slas/$SLA_ORDERS_ID" | python3 -m json.tool
echo

echo "▶ 6b. SLA-Details: payments"
curl -s "$API/slas/$SLA_PAYMENTS_ID" | python3 -m json.tool
echo

# ==========================================================================
# Teil 7: Dashboard — Aggregierte Metriken
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 7: Platform-Dashboard (Alle Metriken)"
echo "═══════════════════════════════════════════════════════════════════"
echo

curl -s "$API/dashboard" | python3 -m json.tool
echo

# ==========================================================================
# Teil 8: SLA-Breach Simulation
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 8: SLA-Breach Simulation (Keine neuen Daten → Freshness-Breach)"
echo "═══════════════════════════════════════════════════════════════════"
echo

echo "▶ 8. Warte 2 Sekunden (simuliert Freshness-Timeout)..."
sleep 2

echo "▶ Erneuter SLA-Check für orders (könnte Freshness-Warnung zeigen)"
curl -s -X POST "$API/slas/$SLA_ORDERS_ID/check" | python3 -m json.tool
echo

# ==========================================================================
# Teil 9: Dashboard nach Simulation
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "TEIL 9: Dashboard nach SLA-Checks"
echo "═══════════════════════════════════════════════════════════════════"
echo

curl -s "$API/dashboard" | python3 -m json.tool
echo

# ==========================================================================
# Zusammenfassung
# ==========================================================================
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ SLA Demo abgeschlossen!"
echo "═══════════════════════════════════════════════════════════════════"
echo
echo "📊 SLAs definiert:"
echo "   - orders:    Freshness 1h,  Availability 99.9%  → $SLA_ORDERS_ID"
echo "   - payments:  Freshness 30m, Availability 99.5%  → $SLA_PAYMENTS_ID"
echo "   - shipments: Freshness 24h, Availability 95.0%  → $SLA_SHIPMENTS_ID"
echo
echo "💡 Wichtige Konzepte:"
echo "   ✓ Freshness SLA: Daten-Aktualität (wann kam letzter Batch?)"
echo "   ✓ Availability SLA: Mindest-Verfügbarkeit (Uptime-Garantie)"
echo "   ✓ SLA-Check: Automatische Prüfung + Breach-Detection"
echo "   ✓ Dashboard: Zentrale Metriken-Übersicht"
echo
echo "🎯 Use Cases:"
echo "   - Critical Datasets: orders, payments → hohe SLAs"
echo "   - Standard Datasets: shipments → moderate SLAs"
echo "   - Alerting: SLA-Breaches trigger Notifikationen"
echo "   - Compliance: SLA-Historie als Audit-Trail"
echo
