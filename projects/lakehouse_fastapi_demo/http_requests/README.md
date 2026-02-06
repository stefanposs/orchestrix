# Lakehouse Demo — HTTP Request Scripts

Collection of shell scripts demonstrating all features of the Lakehouse FastAPI Demo. Each script shows a specific workflow or feature set.

## 📋 Overview

| Script | Focus | Complexity | Duration |
|--------|-------|------------|----------|
| `e2e_happy_path.sh` | Basic Workflow | ⭐ Beginner | ~10s |
| `e2e_extended_happy_path.sh` | Complete Feature Set | ⭐⭐ Intermediate | ~20s |
| `executor_demo.sh` | Multi-Backend Execution | ⭐⭐⭐ Advanced | ~15s |
| `sla_demo.sh` | SLA Monitoring & Dashboard | ⭐⭐ Intermediate | ~15s |
| `pipeline_demo.sh` | One-Shot Automation | ⭐⭐ Intermediate | ~12s |
| `quarantine_demo.sh` | Error Recovery Workflow | ⭐⭐ Intermediate | ~10s |
| `replay_and_events_demo.sh` | Event Sourcing & Replay | ⭐⭐⭐ Advanced | ~12s |
| `error_cases_demo.sh` | Error Handling & Guards | ⭐ Beginner | ~8s |

---

## 🚀 Quick Start

### Prerequisites
```bash
# Start API
just run-lakehouse

# In new terminal:
cd projects/lakehouse_fastapi_demo/http_requests
```

### Run first demo
```bash
# Basic workflow (recommended for getting started)
./e2e_happy_path.sh
```

---

## 📖 Script Details

### 1. `e2e_happy_path.sh` — Basic Workflow
**Use Case:** Fundamental Lakehouse lifecycle  
**Features:**
- Register dataset
- Create data contract
- Append batch
- DQ + Privacy checks
- Publish & consume batch

**When to use:**
- ✅ First demo/presentation
- ✅ Quick regression tests
- ✅ Onboarding new developers

```bash
./e2e_happy_path.sh
```

---

### 2. `e2e_extended_happy_path.sh` — Complete Feature Set
**Use Case:** All features in one run  
**Features:** Basic workflow + SLA + Executor + Pipeline + Dashboard

**When to use:**
- ✅ Complete feature demos
- ✅ Workshops & training
- ✅ Integration tests (CI/CD)

```bash
./e2e_extended_happy_path.sh
```

---

### 3. `executor_demo.sh` — Multi-Backend Job Execution ⭐ NEW
**Use Case:** Understanding the pluggable Executor layer  
**Features:**
- 4 Backends: Local Python, BigQuery, Spark, dbt
- 3 Job Types: Validation, Anonymization, Publish
- Job status monitoring
- Backend comparison

**When to use:**
- ✅ Understanding Executor feature
- ✅ Evaluating backend choices
- ✅ Performance comparisons

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

### 4. `sla_demo.sh` — Service Level Agreements ⭐ NEW
**Use Case:** SLA monitoring & platform dashboard  
**Features:**
- Freshness SLAs (data actuality)
- Availability SLAs (uptime guarantee)
- SLA checks & breach detection
- Aggregated dashboard metrics

**When to use:**
- ✅ Demonstrating SLA feature
- ✅ Showing data governance
- ✅ Compliance workflows

**Highlights:**
```bash
# Critical Dataset: 99.9% Availability, 1h Freshness
POST /slas {"dataset":"orders","freshness_hours":1,"availability_percent":99.9}

# Check SLA
POST /slas/{id}/check

# Dashboard with all metrics
GET /dashboard
```

```bash
./sla_demo.sh
```

---

### 5. `pipeline_demo.sh` — One-Shot Automation ⭐ NEW
**Use Case:** Automated batch processing  
**Features:**
- Pipeline endpoint (1 call instead of 5)
- Ingest → Validate → Privacy → Publish
- Custom executor backends
- Parallel batch processing

**When to use:**
- ✅ Showing CI/CD integration
- ✅ Demonstrating self-service platform
- ✅ Evaluating batch automation

**Highlights:**
```bash
# Manual: 5 API calls
POST /batches/append
POST /batches/{id}/validate
POST /batches/{id}/privacy-check
POST /batches/{id}/publish

# Pipeline: 1 API call ✅
POST /pipeline/run {"dataset":"...", "contract_id":"...", "file_url":"..."}
```

```bash
./pipeline_demo.sh
```

---

### 6. `quarantine_demo.sh` — Error Recovery
**Use Case:** Isolate & correct faulty batches  
**Features:**
- Quarantine batch
- Check publish blockade
- Release quarantine
- Re-validation & publish

**When to use:**
- ✅ Demonstrating error handling
- ✅ Showing data quality workflows
- ✅ Incident management

```bash
./quarantine_demo.sh
```

---

### 7. `replay_and_events_demo.sh` — Event Sourcing
**Use Case:** Understanding event store & replay  
**Features:**
- Query event log
- Filter events (by type, aggregate ID)
- Replay for aggregates
- Demonstrate audit trail

**When to use:**
- ✅ Explaining event sourcing
- ✅ Debugging & troubleshooting
- ✅ Compliance audits

```bash
./replay_and_events_demo.sh
```

---

### 8. `error_cases_demo.sh` — Domain Guards
**Use Case:** Error handling & validation  
**Features:**
- Detect duplicates (409 Conflict)
- Not Found (404)
- Invalid state transitions (422)
- Test guard validation

**When to use:**
- ✅ Demonstrating robustness
- ✅ Documenting error handling
- ✅ Showing defensive programming

```bash
./error_cases_demo.sh
```

---

## 🎯 Recommended Demo Sequence

### For Presentations / Workshops:

1. **Understand basics** → `e2e_happy_path.sh`
2. **SLA feature** → `sla_demo.sh`
3. **Executor layer** → `executor_demo.sh`
4. **Pipeline automation** → `pipeline_demo.sh`
5. **Error handling** → `quarantine_demo.sh`
6. **Event sourcing** → `replay_and_events_demo.sh`

### For Testing:

```bash
# Quick smoke test
./e2e_happy_path.sh

# Full integration test
./e2e_extended_happy_path.sh

# Feature-specific tests
./executor_demo.sh
./sla_demo.sh
./pipeline_demo.sh
```

---

## 🛠️ Technische Details

### Dependencies
- `curl` — HTTP requests
- `python3` — JSON parsing (via `json.tool`)
- `bash` — Shell scripting

### API Base URL
Default: `http://localhost:8000`  
Change via: `export API="http://your-host:8000"`

### Output Format
All scripts use `python3 -m json.tool` for readable JSON formatting.

### Error Handling
All scripts use `set -euo pipefail` for:
- Abort on error (`-e`)
- Unbound variable protection (`-u`)
- Pipeline error propagation (`-o pipefail`)

---

## 📊 Feature Matrix

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

### GitHub Actions Example
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

### GitLab CI Example
```yaml
lakehouse_tests:
  script:
    - just run-lakehouse &
    - sleep 5
    - cd projects/lakehouse_fastapi_demo/http_requests
    - ./e2e_extended_happy_path.sh
```

---

## 📝 Creating Your Own Scripts

### Template
```bash
#!/bin/bash
set -euo pipefail
API="http://localhost:8000"

echo "╔═══════════════════════════════════════════╗"
echo "║   My Custom Demo                        ║"
echo "╚═══════════════════════════════════════════╝"

# Setup
echo "▶ Setup..."
# ... your code ...

# Demo steps
echo "▶ 1. First step"
curl -s -X POST "$API/..." | python3 -m json.tool

echo "✅ Demo completed!"
```

---

## 🐛 Troubleshooting

### API not reachable
```bash
# Check API status
curl http://localhost:8000/health

# Restart API
just run-lakehouse
```

### JSON parsing errors
```bash
# python3 available?
python3 --version

# Alternative: use jq
curl -s "$API/datasets" | jq .
```

### Script permissions
```bash
# Set execution rights
chmod +x *.sh
```

---

## 📚 Further Resources

- **API Documentation:** http://localhost:8000/docs
- **MkDocs:** [Lakehouse Demo Guide](../../../docs/demos/lakehouse/)
- **README:** [Project README](../README.md)
- **E2E Analysis:** [E2E_ANALYSIS.md](./E2E_ANALYSIS.md)

---

## 🤝 Contributing

New demo scripts are welcome! Follow the template above and create a PR.

**Checklist:**
- [ ] `set -euo pipefail` header
- [ ] Execution rights (`chmod +x`)
- [ ] JSON formatting via `python3 -m json.tool`
- [ ] Setup + cleanup steps
- [ ] Comments for each step
- [ ] Success message at the end

---

**Happy Testing! 🚀**
