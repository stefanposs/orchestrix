# Prozess- und Event-/Command-Katalog

Dieser Katalog dokumentiert alle Kernprozesse, Events und Commands der Lakehouse-Demo-API sowie deren Abhängigkeiten und Zusammenhänge.

---

## Übersicht: API-Endpunkte & Prozesse

### Datasets (`/datasets`)

| Methode | Endpoint          | Command / Aktion       | Beschreibung                          | Events                     |
|---------|-------------------|------------------------|---------------------------------------|----------------------------|
| POST    | `/datasets`       | RegisterDataset        | Neues Dataset mit Schema registrieren | DatasetRegistered          |
| GET     | `/datasets`       | —                      | Alle Datasets auflisten               | —                          |
| GET     | `/datasets/{name}`| —                      | Dataset-Details abrufen               | —                          |

### Contracts (`/contracts`)

| Methode | Endpoint       | Command / Aktion   | Beschreibung                               | Events              |
|---------|----------------|--------------------|--------------------------------------------|----------------------|
| POST    | `/contracts`   | CreateContract     | Data Contract anlegen (Schema, Retention, Privacy/Quality Rules) | DataContractDefined  |
| GET     | `/contracts`   | —                  | Alle Contracts auflisten                   | —                    |

### Batches (`/batches`) — Dateningestion & Lifecycle

| Methode | Endpoint                         | Command / Aktion   | Beschreibung                                    | Events                                         |
|---------|----------------------------------|--------------------|-------------------------------------------------|------------------------------------------------|
| POST    | `/batches/append`                | AppendData         | Daten-Batch an Dataset anfügen (Hauptingestion) | AppendIngestionRequested → DataAppended        |
| POST    | `/batches/{batch_id}/quarantine` | QuarantineBatch    | Batch als fehlerhaft markieren                  | BatchQuarantined                               |
| POST    | `/batches/{batch_id}/release`    | ReleaseQuarantine  | Quarantäne aufheben                             | QuarantineReleased                             |
| POST    | `/batches/{batch_id}/validate`   | RunQualityCheck    | Datenqualität prüfen                            | QualityCheckPassed / QualityCheckFailed        |
| POST    | `/batches/{batch_id}/privacy-check` | RunPrivacyCheck | Privacy/Compliance prüfen                       | PrivacyCheckPassed / PrivacyCheckFailed        |
| POST    | `/batches/{batch_id}/publish`    | PublishData        | Batch für Konsum freigeben                      | DataPublished                                  |
| POST    | `/batches/{batch_id}/consume`    | ConsumeBatch       | Batch konsumieren (signed Download-URL)         | ConsumptionGranted                             |
| GET     | `/batches`                       | —                  | Alle Batches auflisten (optional Filter)        | —                                              |

### Events (`/events`)

| Methode | Endpoint         | Command / Aktion   | Beschreibung                              | Events                              |
|---------|------------------|--------------------|--------------------------------------------|--------------------------------------|
| POST    | `/events/replay` | RequestReplay      | Events für Dataset replayed (State Rebuild) | ReplayRequested → ReplayCompleted    |
| GET     | `/events`        | —                  | Event-Log abfragen (Filter: batch, dataset, type) | —                              |

---

## Prozess-Flow (vereinfacht)

```
1. POST /datasets          → DatasetRegistered
2. POST /contracts         → DataContractDefined
3. POST /batches/append    → AppendIngestionRequested → DataAppended
   └→ POST /batches/{id}/validate      → QualityCheckPassed
   └→ POST /batches/{id}/privacy-check → PrivacyCheckPassed
   └→ POST /batches/{id}/publish       → DataPublished
4. POST /batches/{id}/consume          → ConsumptionGranted
5. POST /events/replay                 → ReplayCompleted
```

---

## Abhängigkeiten & Ketten

- **AppendData** benötigt: registriertes Dataset + existierender Contract
- **Validate / Privacy-Check** operiert auf existierendem Batch
- **Publish** setzt (optional) bestandene Quality/Privacy Checks voraus
- **Consume** ist nur für veröffentlichte Batches möglich
- **QuarantineBatch** kann jederzeit auf einem Batch ausgelöst werden
- **Replay** baut den Zustand eines Datasets aus dem Event-Log neu auf

---

## Beispiel: End-to-End Flow für neuen Batch

```
1. POST /datasets          {"name": "sales", "schema": {"id": "int", "amount": "float"}}
2. POST /contracts         {"dataset": "sales", "retention_days": 365}
3. POST /batches/append    {"dataset": "sales", "contract_id": "contract-xxx", "file_url": "s3://..."}
4. POST /batches/{id}/validate      {"quality_rules": {"amount": ">0"}}
5. POST /batches/{id}/privacy-check {"privacy_rules": {"email": "mask"}}
6. POST /batches/{id}/publish
7. POST /batches/{id}/consume       {"consumer": "analytics-team"}
```

---

## Design-Prinzipien

- **RESTful**: Ressourcen-orientierte URLs, HTTP-Verben statt Action-Namen
- **Event Sourced**: Jeder Command erzeugt mindestens ein Event
- **Aggregate-verdrahtet**: Endpoints nutzen Domain Aggregates (Dataset, Contract, Batch)
- **Audit Trail**: Alle Events landen im Event-Log und sind über `/events` abfragbar
- **Modular**: Prozesse sind unabhängig erweiterbar (z.B. neue Checks, Anonymisierung)
