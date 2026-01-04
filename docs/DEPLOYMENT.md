# Orchestrix Deployment Guide

> **⚠️ This document is being superseded by our comprehensive deployment guides:**
> - **[Production Deployment Guide](mkdocs/guide/production-deployment.md)** - Complete guide for small/medium/large projects
> - **[Production Readiness Guide](mkdocs/guide/production-ready.md)** - Detailed production checklist
> 
> The information below remains accurate for PyPI publishing workflow.

---

## ✅ Current Status

Orchestrix v0.1.0 ist jetzt **production-ready** und bereit für die Veröffentlichung auf PyPI!

### Was ist fertig:
- ✅ Core Framework mit CloudEvents-kompatiblen Messages
- ✅ InMemory Infrastructure (Bus & Store)
- ✅ 100% Test Coverage (17 Tests)
- ✅ Type-Safe mit mypy strict mode
- ✅ Linting mit ruff (0 Errors)
- ✅ Code Formatting mit ruff
- ✅ Enterprise-ready Packaging
- ✅ GitHub Actions CI/CD
- ✅ Dokumentation (MkDocs)
- ✅ Community Files (Contributing, Code of Conduct, Security)
- ✅ Justfile für Developer Workflow
- ✅ Git Repository initialisiert

## 🚀 Nächste Schritte für PyPI-Veröffentlichung

### 1. GitHub Repository erstellen

```bash
# In GitHub Web UI: Create new repository "orchestrix"
# Dann lokal:
git remote add origin git@github.com:YOUR_USERNAME/orchestrix.git
git branch -M main
git push -u origin main
```

### 2. PyPI Account vorbereiten

1. Account erstellen auf [pypi.org](https://pypi.org/account/register/)
2. 2FA aktivieren (erforderlich für Trusted Publishers)
3. API Token erstellen unter [Account Settings → API tokens](https://pypi.org/manage/account/)

### 3. GitHub Secrets konfigurieren

Gehe zu: `Settings → Secrets and variables → Actions`

Füge hinzu:
- `PYPI_API_TOKEN`: Dein PyPI API Token

### 4. Dokumentation deployen

#### Option A: GitHub Pages

```bash
# Im Repository Settings → Pages
# Source: GitHub Actions
# Dann:
just docs-deploy
```

#### Option B: ReadTheDocs

1. Account erstellen auf [readthedocs.org](https://readthedocs.org/)
2. Import GitHub Repository
3. Build triggern

### 5. Release erstellen

```bash
# Tag erstellen
git tag -a v0.1.0 -m "Release v0.1.0: Initial release"
git push origin v0.1.0

# In GitHub:
# Releases → Create a new release
# Choose tag: v0.1.0
# Release title: "Orchestrix v0.1.0"
# Description: Copy from CHANGELOG.md
# ✅ Set as latest release
# Publish release
```

Das triggert automatisch:
- ✅ GitHub Actions Workflow `.github/workflows/publish.yml`
- ✅ Build des Packages
- ✅ Upload zu PyPI
- ✅ Package ist verfügbar unter `pip install orchestrix`

### 6. Installation testen

```bash
# In einem neuen Terminal/Projekt:
pip install orchestrix

# Test:
python -c "from orchestrix import Message, InMemoryMessageBus; print('✅ Works!')"
```

## 📦 Lokales Testing vor Release

```bash
# QA Suite laufen lassen
just qa

# Package bauen
just build

# Package testen
python -m venv test_env
source test_env/bin/activate
pip install dist/orchestrix-0.1.0-py3-none-any.whl
python -c "from orchestrix import Message; print(Message)"
deactivate
rm -rf test_env
```

## 🔧 Development Workflow

```bash
# Setup (nur einmal)
just setup

# Entwickeln
just fix      # Auto-format und auto-fix
just check    # Lint + Format-Check + Typecheck

# Testen
just test           # Tests laufen lassen
just test-cov       # Tests mit Coverage Report
just test-watch     # Tests im Watch-Mode

# QA
just qa       # Komplette QA Suite

# Build
just build    # Package bauen

# Alles zusammen (CI simulation)
just ci       # Clean + Sync + Pre-commit + QA + Build
```

## 📊 Package Statistiken

- **Größe**: ~8.8 KB (Wheel), ~11 KB (Source)
- **Python**: 3.9-3.13
- **Dependencies**: Keine (pure Python)
- **Test Coverage**: 100%
- **Type Coverage**: 100% (mypy strict)
- **Lines of Code**: ~71 statements (core)

## 🎯 Nächste Features (für v0.2.0)

- [ ] Async MessageBus Implementation
- [ ] Async EventStore Implementation
- [ ] Redis-backed Infrastructure
- [ ] SQLAlchemy EventStore
- [ ] Saga Pattern Support
- [ ] Retry & Error Handling Middleware
- [ ] Message Validation
- [ ] Tracing & Observability
- [ ] More Examples & Tutorials

## 📝 Checkliste vor PyPI Upload

- [x] Tests laufen (100% Coverage)
- [x] Type-Check passt
- [x] Linting passt
- [x] README.md ist vollständig
- [x] LICENSE ist korrekt (MIT)
- [x] CHANGELOG.md ist aktuell
- [x] pyproject.toml Metadata korrekt
- [x] examples/ funktionieren
- [ ] GitHub Repository erstellt
- [ ] GitHub Actions CI läuft grün
- [ ] Documentation deployed
- [ ] PyPI Account erstellt
- [ ] PyPI API Token konfiguriert

## 🆘 Troubleshooting

### "Permission denied" beim PyPI Upload
→ Prüfe ob `PYPI_API_TOKEN` Secret korrekt gesetzt ist

### GitHub Actions schlägt fehl
→ Prüfe ob alle Tests lokal mit `just ci` durchlaufen

### Package nicht gefunden nach Upload
→ Warte 1-2 Minuten, PyPI braucht Zeit für Indexing

### Import-Fehler nach Installation
→ Prüfe ob `__init__.py` alle exports hat (siehe `__all__`)

## 📚 Weitere Ressourcen

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [MkDocs Documentation](https://www.mkdocs.org/)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
