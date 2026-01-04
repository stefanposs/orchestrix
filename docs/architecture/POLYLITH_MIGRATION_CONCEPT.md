# Architecture Concept: Polylith Migration Strategy

**Status:** DRAFT / EVALUATION  
**Date:** 2026-01-04  
**Author:** Stefan Poss  
**Context:** Evaluation of Polylith Architecture for Orchestrix Framework

---

## 1. Management Summary

Orchestrix ist aktuell als klassisches, monolithisches Python-Package strukturiert. Während die logische Architektur (Protocols, Ports & Adapters) bereits hochgradig modular ist, spiegelt die physische Projektstruktur dies nicht wider. 

Die **Polylith-Architektur** bietet einen Ansatz, diese Modularität auch physisch zu erzwingen, die Build-Zeiten zu optimieren und die Entwicklung von Erweiterungen (neue Backends) skalierbar zu gestalten. Dieses Dokument analysiert die Implikationen einer Migration.

---

## 2. AEK-Analyse (Ausgangslage - Erkenntnis - Konsequenz)

### A - Ausgangslage (Situation)

*   **Struktur:** Monolithisches Layout (`src/orchestrix/{core,infrastructure}`).
*   **Kopplung:** Logisch entkoppelt (via Protocols), aber physisch liegen alle Dateien im selben Import-Pfad. Ein Entwickler kann versehentlich `infrastructure`-Code in `core` importieren, ohne dass es sofort auffällt (außer durch Review).
*   **Dependencies:** Alle Abhängigkeiten (Postgres, OpenTelemetry, etc.) werden in einer einzigen `pyproject.toml` verwaltet. Dies führt zu einer wachsenden Liste von `optional-dependencies`.
*   **Testing:** Bei jeder Änderung laufen oft alle Tests, da schwer zu isolieren ist, welche Teile betroffen sind.
*   **Erweiterbarkeit:** Das Hinzufügen neuer Backends (z.B. Kafka, Redis) bläht das Haupt-Repository und die Abhängigkeiten weiter auf.

### E - Erkenntnis (Insight)

*   **Architektur-Match:** Orchestrix folgt bereits dem "Hexagonal Architecture" Pattern. Polylith ist die physische Manifestation dieses Patterns für Monorepos. Es passt konzeptionell perfekt.
*   **Skalierungsproblem:** Wenn Orchestrix wächst (z.B. 10 verschiedene EventStores), wird das aktuelle Projekt unübersichtlich. Nutzer installieren oft "zu viel", auch wenn sie nur Core brauchen.
*   **Developer Experience:** Die aktuelle Struktur macht es schwer, *nur* an einem Modul (z.B. `postgres_store`) zu arbeiten und nur dessen Tests auszuführen, ohne den Kontext des Gesamtsystems zu laden.
*   **Wiederverwendbarkeit:** Die Beispiel-Codes (`examples/`) sind aktuell nur Skripte. In Polylith wären sie eigenständige "Bases", die wie echte Apps behandelt, gebaut und deployed werden könnten.

### K - Konsequenz (Consequence)

*   **Migration empfohlen (Langfristig):** Um Orchestrix von einer "Library" zu einem "Ökosystem" zu entwickeln, ist Polylith der richtige Weg.
*   **Strikte Trennung:** Wir müssen den Code in `components` (Logik) und `bases` (Einstiegspunkte) zerlegen.
*   **Build-Prozess:** Der Build-Prozess ändert sich fundamental. Statt einem `setup.py`/`pyproject.toml` gibt es eine Workspace-Konfiguration, die "Projects" (deploybare Artefakte) aus Komponenten zusammenbaut.
*   **Investition:** Eine Migration kostet initial Zeit (Refactoring, Tooling-Setup), spart aber langfristig Wartungsaufwand bei wachsender Komplexität.

---

## 3. Ziel-Architektur (To-Be)

Wenn wir Orchestrix auf Polylith umstellen, sieht der Workspace wie folgt aus:

### 3.1 Workspace Layout

```text
orchestrix-workspace/
├── workspace.toml             # Polylith Config
├── pyproject.toml             # Shared Dev-Dependencies (Ruff, Mypy, Pytest)
│
├── components/                # THE BRICKS (Wiederverwendbare Logik)
│   ├── core/                  # Das Herzstück (Interfaces, Message, Aggregate)
│   │   ├── src/orchestrix/core/...
│   │   └── pyproject.toml     # Keine externen Deps!
│   │
│   ├── infrastructure_pg/     # Postgres Adapter
│   │   ├── src/orchestrix/infra/postgres/...
│   │   └── pyproject.toml     # Dep: asyncpg, component: core
│   │
│   ├── infrastructure_mem/    # InMemory Adapter
│   │   ├── src/orchestrix/infra/memory/...
│   │   └── pyproject.toml     # Dep: component: core
│   │
│   └── observability/         # Tracing/Metrics
│       ├── src/orchestrix/observability/...
│       └── pyproject.toml     # Dep: opentelemetry, component: core
│
├── bases/                     # THE GLUE (Einstiegspunkte)
│   ├── examples_banking/      # Banking Demo App
│   │   └── src/examples/banking/...
│   │
│   └── cli/                   # Orchestrix CLI Tool (Zukunftsmusik)
│       └── src/orchestrix/cli/...
│
└── projects/                  # THE ARTIFACTS (Deployables)
    ├── orchestrix_lib/        # Das Haupt-PyPI Package
    │   └── pyproject.toml     # Bündelt: core, infra_mem (als default)
    │
    ├── orchestrix_full/       # "Batteries Included" Package
    │   └── pyproject.toml     # Bündelt: core, infra_*, observability
    │
    └── banking_demo/          # Deploybarer Service
        └── pyproject.toml     # Bündelt: examples_banking, core, infra_pg
```

### 3.2 Die Vorteile dieser Struktur

1.  **Physische Entkopplung:** `core` *kann* technisch gar nicht auf `asyncpg` zugreifen, da es in einer anderen Komponente liegt und nicht im Pfad ist (außer im assemblierten Projekt).
2.  **Feingranulare Tests:** `uv run polylith test` führt nur Tests für Komponenten aus, die sich geändert haben.
3.  **Flexible Distribution:** Wir können entscheiden, ob wir ein monolithisches `orchestrix` Paket auf PyPI veröffentlichen (das alles bündelt) oder modulare Pakete (`orchestrix-core`, `orchestrix-postgres`).

### 3.3 Die Goldenen Regeln (Dependency Flow)

Damit Polylith funktioniert, gelten strikte Import-Regeln:

| Wer? | Darf importieren... | Darf NICHT importieren... | Grund |
| :--- | :--- | :--- | :--- |
| **Base** | Components | Andere Bases | Bases sind isolierte Einstiegspunkte. Geteilter Code muss in eine Component. |
| **Component** | Andere Components | Bases | Components sind wiederverwendbare Bausteine. Sie dürfen nichts von der App wissen, die sie nutzt. |
| **Project** | Bases, Components | - | Projects sind nur Konfigurationen (TOML), kein Code. |

**Beispiel:**
*   ❌ `bases/cli` importiert `bases/web_api` (Verboten!)
*   ✅ `bases/cli` importiert `components/core` (Erlaubt)
*   ✅ `components/postgres` importiert `components/core` (Erlaubt)

### 3.4 Technische Umsetzung mit uv Workspaces

Da wir bereits `uv` nutzen, ist die Verwendung von **uv Workspaces** der empfohlene Weg. Dies vermeidet externe Plugins (wie bei Poetry) und nutzt native Standards.

**Die Rolle der Root `pyproject.toml`:**
Sie ist die "Zentrale", die alle Teile zusammenhält. Ohne sie wüssten die Tools nicht, wo der Code liegt.

```toml
# Root pyproject.toml
[project]
name = "orchestrix-workspace"
requires-python = ">=3.12"

[tool.uv.workspace]
members = [
    "components/*",
    "bases/*",
    "projects/*"
]

[tool.uv.sources]
# Hier mappen wir die lokalen Pfade für die Entwicklung
orchestrix-core = { workspace = true }
orchestrix-postgres = { workspace = true }
```

**Wie es funktioniert:**
1.  **Workspace Definition:** `tool.uv.workspace.members` sagt `uv`, in welchen Ordnern es nach Paketen suchen soll.
2.  **Development:** Wenn du `uv sync` im Root ausführst, installiert `uv` alle Components und Bases im "Editable Mode".
3.  **Imports:** Du kannst in deinem Code `import orchestrix.core` schreiben, und `uv` sorgt dafür, dass Python die Dateien in `components/core/src/orchestrix/core` findet.

---

## 4. Migrations-Strategie

Da Orchestrix bereits v0.1.0 (Production Ready) ist, sollte die Migration schrittweise erfolgen ("Strangler Fig Pattern" für Repos).

### Phase 1: Vorbereitung (Parallelbetrieb)
1.  **Tooling:** Wir setzen voll auf `uv` Workspaces.
2.  **Struktur:** Ordner `components`, `bases`, `projects` anlegen.
3.  **Config:** Root `pyproject.toml` auf Workspace-Modus umstellen (siehe oben).

### Phase 2: Extraktion "Core"
1.  Verschieben von `src/orchestrix/core` nach `components/core`.
2.  Erstellen eines `projects/orchestrix_lib`, das vorerst noch den Rest als "Legacy" enthält, aber `core` als Komponente einbindet.
3.  Anpassen der CI-Pipeline.

### Phase 3: Extraktion "Infrastructure"
1.  Zerlegen von `src/orchestrix/infrastructure` in `components/infrastructure_postgres`, `components/infrastructure_memory`, etc.
2.  Jede Komponente bekommt ihre eigenen Tests.

### Phase 4: Cleanup
1.  Löschen des alten `src/` Ordners.
2.  Vollständige Umstellung der CI auf Polylith-Workflows.

---

## 5. Entscheidungsempfehlung

| Kriterium | Aktuell (Monolith) | Polylith (Modular) | Empfehlung |
|-----------|--------------------|--------------------|------------|
| **Komplexität Setup** | Niedrig | Mittel | Monolith (aktuell) |
| **Wartbarkeit (Skalierung)** | Sinkend bei Größe | Konstant hoch | Polylith |
| **Build-Geschwindigkeit** | Langsam (alles testen) | Schnell (inkrementell) | Polylith |
| **Architektur-Einhaltung** | Konvention | Erzwungen | Polylith |
| **Onboarding neuer Devs** | Einfach | Lernkurve | Monolith |

### Fazit des Lead Architects

**Warte mit der Migration bis Version 0.5 oder 1.0.**

Aktuell ist der Overhead für das Setup höher als der Nutzen, da wir "nur" ca. 30 Dateien haben. Die aktuelle Struktur ist sauber genug.

**Trigger für die Migration sollten sein:**
1.  Wir fügen 2-3 weitere schwere Infrastruktur-Backends hinzu (Kafka, Redis, Mongo).
2.  Wir wollen eine CLI oder einen Admin-UI-Server im selben Repo entwickeln.
3.  Die CI-Zeiten steigen über 5-10 Minuten.

Bis dahin: **Keep it simple.** Aber behalte Polylith als Zielbild im Hinterkopf.
