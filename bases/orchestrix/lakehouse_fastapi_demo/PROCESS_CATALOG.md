# Prozess- und Event-/Command-Katalog

Dieser Katalog dokumentiert alle Kernprozesse, Events und Commands der Lakehouse-Demo-API sowie deren Abhängigkeiten und Zusammenhänge.

---

## Übersicht: Hauptprozesse

| Prozess            | Command/Event                | Beschreibung                                      | Abhängigkeiten / Folge-Events           |
|--------------------|-----------------------------|---------------------------------------------------|-----------------------------------------|
| Register Dataset   | RegisterDataset (Command)    | Registriert ein neues Dataset mit Schema          | DatasetRegistered (Event)               |
| Register Contract  | CreateContract (Command)     | Legt Vertrag/Retention für Dataset an             | ContractCreated (Event)                 |
| Upload Batch       | AppendBatch (Command)        | Lädt Datenbatch (CSV) hoch                        | BatchAppended (Event)                   |
| Replay            | Replay (Command)             | Reprocess aller Batches für ein Dataset           | ReplayStarted, ReplayCompleted (Events) |
| Quarantine Batch   | QuarantineBatch (Command)    | Markiert Batch als fehlerhaft                     | BatchQuarantined (Event)                |
| Data Quality Check | RunDQ (Command)              | Prüft Datenqualität für Batch                     | DQChecked (Event)                       |
| Privacy Check      | RunPrivacy (Command)         | Prüft Privacy/Compliance für Batch                | PrivacyChecked (Event)                  |
| Publish Batch      | PublishBatch (Command)       | Stellt Batch für Konsum bereit                    | BatchPublished (Event)                  |
| Consume Batch      | ConsumeBatch (Command)       | Liefert Batch als CSV (signed URL)                | BatchConsumed (Event)                   |

---

## Prozess-Flow (vereinfacht)

1. **RegisterDataset** → *DatasetRegistered*
2. **CreateContract** → *ContractCreated*
3. **AppendBatch** → *BatchAppended* → (optional: *RunDQ*, *RunPrivacy*) → *PublishBatch* → *BatchPublished*
4. **Replay** → *ReplayStarted* → (re-appends alle Batches) → *ReplayCompleted*
5. **ConsumeBatch** → *BatchConsumed*

---

## Abhängigkeiten & Ketten

- **AppendBatch** triggert nach erfolgreichem Upload meist DQ/Privacy-Checks und dann Publish
- **Replay** kann mehrere Batches erneut durch den gesamten Pipeline-Prozess schicken
- **QuarantineBatch** kann von DQ/Privacy-Checks ausgelöst werden
- **ConsumeBatch** ist nur für veröffentlichte Batches möglich

---

## Beispiel: Event-Flow für neuen Batch

1. AppendBatch (Command)
2. BatchAppended (Event)
3. RunDQ (Command) → DQChecked (Event)
4. RunPrivacy (Command) → PrivacyChecked (Event)
5. PublishBatch (Command) → BatchPublished (Event)
6. ConsumeBatch (Command) → BatchConsumed (Event)

---

## Hinweise
- Jeder Command erzeugt mindestens ein Event (Event Sourcing)
- Events sind auditierbar und rekonstruieren den Systemzustand
- Die Prozesse sind modular und können beliebig erweitert werden (z.B. weitere Checks, neue Events)
