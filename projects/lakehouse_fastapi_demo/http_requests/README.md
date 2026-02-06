# Lakehouse Demo — HTTP Request Scripts

Sammlung von Shell-Skripten zur Demonstration aller Features der Lakehouse FastAPI Demo. Jedes Skript zeigt einen spezifischen Workflow oder Feature-Set.

## 📋 Übersicht

| Skript | Fokus | Komplexität | Dauer |
|--------|-------|-------------|-------|
| `e2e_happy_path.sh` | Basis-Workflow | ⭐ Beginner | ~10s |
| `e2e_extended_happy_path.sh` | Vollständiges Feature-Set | ⭐⭐ Intermediate | ~20s |
| `executor_demo.sh` | Multi-Backend Execution | ⭐⭐⭐ Advanced | ~15s |
| `sla_demo.sh` | SLA Monitoring & Dashboard | ⭐⭐ Intermediate | ~15s |
| `pipeline_demo.sh` | One-Shot Automation | ⭐⭐ Intermediate | ~12s |
| `quarantine_demo.sh` | Error Recovery Workflow | ⭐⭐ Intermediate | ~10s |
| `replay_and_events_demo.sh` | Event Sourcing & Replay | ⭐⭐⭐ Advanced | ~12s |
| `error_cases_demo.sh` | Error Handling & Guards | ⭐ Beginner | ~8s |

---

## 🚀 Quick Start

### Voraussetzungen
```bash
# API starten
just run-lakehouse

# In neuem Terminal:
cd projects/lakehouse_fastapi_demo/http_requests
```

### Erstes Demo ausführen
```bash
# Basis-Workflow (empfohlen für Einstieg)
./e2e_happy_path.sh
```

---

## 📖 Skript-Details

### 1. `e2e_happy_path.sh` — Basis-Workflow
**Use Case:** Grundlegender Lakehouse-Lifecycle  
**Features:**
- Dataset registrieren
- Datenvertrag anlegen
- Batch anhängen
- DQ + Privacy Checks
- Batch publishen & konsumieren

**Wann nutzen:**
- ✅ Erste Demo/Präsentation
- ✅ Schnelle Regressionstests
- ✅ Onboarding neuer Entwickler

```bash
./e2e_happy_path.sh
```

---

### 2. `e2e_extended_happy_path.sh` — Vollständiges Feature-Set
**Use Case:** Alle Features in einem Durchlauf  
**Features:** Basis-Workflow + SLA + Executor + Pipeline + Dashboard

**Wann nutzen:**
- ✅ Vollständige Feature-Demos
- ✅ Workshops & Trainings
- ✅ Integration Tests (CI/CD)

```bash
./e2e_extended_happy_path.sh
```

---

### 3. `executor_demo.sh` — Multi-Backend Job Execution ⭐ NEU
**Use Case:** Pluggable Executor-Layer verstehen  
**Features:**
- 4 Backends: Local Python, BigQuery, Spark, dbt
- 3 Job-Typen: Validation, Anonymization, Publish
- Job-Status Monitoring
- Backend-Vergleich

**Wann nutzen:**
- ✅ Executor-Feature verstehen
- ✅ Backend-Auswahl evaluieren
- ✅ Performance-Vergleiche

**Highlights:**
```bash
# Local Python: Schnell, in-process
POST /executor/jobs {"backend": "local_python"}

# BigQuery: Cloud-native, skalierbar
POST /executor/jobs {"backend": "bigquery"}

# Spark: Distributed, große Batches
POST /executor/jobs {"backend": "spark"}

# dbt: SQL-based Transforms
POST /executor/jobs {"backend": "dbt"}
```

```bash
./executor_demo.sh
```

---

### 4. `sla_demo.sh` — Service Level Agreements ⭐ NEU
**Use Case:** SLA-Monitoring & Platform-Dashboard  
**Features:**
- Freshness SLAs (Daten-Aktualität)
- Availability SLAs (Uptime-Garantie)
- SLA-Checks & Breach-Detection
- Aggregierte Dashboard-Metriken

**Wann nutzen:**
- ✅ SLA-Feature demonstrieren
- ✅ Data Governance zeigen
- ✅ Compliance-Workflows

**Highlights:**
```bash
# Critical Dataset: 99.9% Availability, 1h Freshness
POST /slas {"dataset":"orders","freshness_hours":1,"availability_percent":99.9}

# SLA prüfen
POST /slas/{id}/check

# Dashboard mit allen Metriken
GET /dashboard
```

```bash
./sla_demo.sh
```

---

### 5. `pipeline_demo.sh` — One-Shot Automation ⭐ NEU
**Use Case:** Automatisierte Batch-Verarbeitung  
**Features:**
- Pipeline-Endpunkt (1 Call statt 5)
- Ingest → Validate → Privacy → Publish
- Custom Executor-Backends
- Parallel Batch-Processing

**Wann nutzen:**
- ✅ CI/CD Integration zeigen
- ✅ Self-Service Platform demonstrieren
- ✅ Batch-Automation evaluieren

**Highlights:**
```bash
# Manuell: 5 API-Calls
POST /batches/append
POST /batches/{id}/validate
POST /batches/{id}/privacy-check
POST /batches/{id}/publish

# Pipeline: 1 API-Call ✅
POST /pipeline/run {"dataset":"...", "contract_id":"...", "file_url":"..."}
```

```bash
./pipeline_demo.sh
```

---

### 6. `quarantine_demo.sh` — Error Recovery
**Use Case:** Fehlerhafte Batches isolieren & korrigieren  
**Features:**
- Batch in Quarantäne setzen
- Publish-Blockade prüfen
- Quarantäne aufheben
- Re-Validation & Publish

**Wann nutzen:**
- ✅ Error-Handling demonstrieren
- ✅ Data Quality Workflows zeigen
- ✅ Incident-Management

```bash
./quarantine_demo.sh
```

---

### 7. `replay_and_events_demo.sh` — Event Sourcing
**Use Case:** Event Store & Replay verstehen  
**Features:**
- Event-Log abfragen
- Events filtern (nach Type, Aggregate-ID)
- Replay für Aggregates
- Audit-Trail demonstrieren

**Wann nutzen:**
- ✅ Event Sourcing erklären
- ✅ Debugging & Troubleshooting
- ✅ Compliance Audits

```bash
./replay_and_events_demo.sh
```

---

### 8. `error_cases_demo.sh` — Domain Guards
**Use Case:** Fehlerbehandlung & Validierung  
**Features:**
- Duplikate erkennen (409 Conflict)
- Not Found (404)
- Invalid State Transitions (422)
- Guard-Validierung testen

**Wann nutzen:**
- ✅ Robustheit demonstrieren
- ✅ Error-Handling dokumentieren
- ✅ Defensive Programming zeigen

```bash
./error_cases_demo.sh
```

---

## 🎯 Empfohlene Demo-Reihenfolge

### Für Präsentationen / Workshops:

1. **Basis verstehen** → `e2e_happy_path.sh`
2. **SLA-Feature** → `sla_demo.sh`
3. **Executor-Layer** → `executor_demo.sh`
4. **Pipeline-Automation** → `pipeline_demo.sh`
5. **Error-Handling** → `quarantine_demo.sh`
6. **Event Sourcing** → `replay_and_events_demo.sh`

### Für Testing:

```bash
# Quick Smoke Test
./e2e_happy_path.sh

# Full Integration Test
./e2e_extended_happy_path.sh

# Feature-Specific Tests
./executor_demo.sh
./sla_demo.sh
./pipeline_demo.sh
```

---

## 🛠️ Technische Details

### Dependencies
- `curl` — HTTP-Requests
- `python3` — JSON-Parsing (via `json.tool`)
- `bash` — Shell-Scripting

### API Base URL
Standardmäßig: `http://localhost:8000`  
Ändern via: `export API="http://your-host:8000"`

### Ausgabe-Format
Alle Skripte nutzen `python3 -m json.tool` für lesbare JSON-Formatierung.

### Error Handling
Alle Skripte nutzen `set -euo pipefail` für:
- Abbruch bei Fehlern (`-e`)
- Unbound-Variable-Schutz (`-u`)
- Pipeline-Fehler-Propagation (`-o pipefail`)

---

## 📊 Feature-Matrix

| Feature | happy_path | extended | executor | sla | pipeline | quarantine | replay | errors |
|---------|:----------:|:--------:|:--------:|:---:|:--------:|:----------:|:------:|:------:|
| Dataset Register | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Contract | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Batch Append | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| DQ Check | ✅ | ✅ | - | ✅ | - | ✅ | - | - |
| Privacy Check | ✅ | ✅ | - | ✅ | - | ✅ | - | - |
| Publish | ✅ | ✅ | - | ✅ | - | ✅ | - | - |
| Consume | ✅ | ✅ | - | ✅ | - | - | - | - |
| **SLA** | - | ✅ | - | ✅ | - | - | - | - |
| **Executor** | - | ✅ | ✅ | - | ✅ | - | - | - |
| **Pipeline** | - | ✅ | - | - | ✅ | - | - | - |
| **Dashboard** | - | ✅ | - | ✅ | - | - | - | - |
| Quarantine | - | - | - | - | - | ✅ | - | ✅ |
| Event Replay | - | - | - | - | - | - | ✅ | - |
| Error Cases | - | - | - | - | - | - | - | ✅ |

---

## 🚦 CI/CD Integration

### GitHub Actions Beispiel
```yaml
- name: Run Lakehouse Demo Tests
  run: |
    just run-lakehouse &
    sleep 5
    cd projects/lakehouse_fastapi_demo/http_requests
    ./e2e_happy_path.sh
    ./executor_demo.sh
    ./sla_demo.sh
```

### GitLab CI Beispiel
```yaml
lakehouse_tests:
  script:
    - just run-lakehouse &
    - sleep 5
    - cd projects/lakehouse_fastapi_demo/http_requests
    - ./e2e_extended_happy_path.sh
```

---

## 📝 Eigene Skripte erstellen

### Template
```bash
#!/bin/bash
set -euo pipefail
API="http://localhost:8000"

echo "╔═══════════════════════════════════════════╗"
echo "║   Mein Custom Demo                        ║"
echo "╚═══════════════════════════════════════════╝"

# Setup
echo "▶ Setup..."
# ... dein Code ...

# Demo-Schritte
echo "▶ 1. Erster Schritt"
curl -s -X POST "$API/..." | python3 -m json.tool

echo "✅ Demo abgeschlossen!"
```

---

## 🐛 Troubleshooting

### API nicht erreichbar
```bash
# API-Status prüfen
curl http://localhost:8000/health

# API neu starten
just run-lakehouse
```

### JSON-Parsing-Fehler
```bash
# python3 verfügbar?
python3 --version

# Alternative: jq nutzen
curl -s "$API/datasets" | jq .
```

### Script-Permissions
```bash
# Ausführungsrechte setzen
chmod +x *.sh
```

---

## 📚 Weitere Ressourcen

- **API-Dokumentation:** http://localhost:8000/docs
- **MkDocs:** [Lakehouse Demo Guide](../../../docs/demos/lakehouse/)
- **README:** [Projekt-README](../README.md)
- **E2E-Analyse:** [E2E_ANALYSIS.md](./E2E_ANALYSIS.md)

---

## 🤝 Beitragen

Neue Demo-Skripte sind willkommen! Folge dem Template oben und erstelle einen PR.

**Checklist:**
- [ ] `set -euo pipefail` Header
- [ ] Ausführungsrechte (`chmod +x`)
- [ ] JSON-Formatierung via `python3 -m json.tool`
- [ ] Setup + Cleanup Schritte
- [ ] Kommentare für jeden Schritt
- [ ] Erfolgs-Message am Ende

---

**Happy Testing! 🚀**
