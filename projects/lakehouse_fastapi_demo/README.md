
## LAKEHOUSE FASTAPI DEMO

Start the server:

```bash
uv run lakehouse_fastapi_demo
```

Example requests:

- **Register dataset:**
	```bash
	curl -X POST http://localhost:8000/datasets -H "Content-Type: application/json" -d '{"name": "sales", "schema": {"id": "int", "amount": "float"}}'
	```
- **Register contract:**
	```bash
	curl -X POST http://localhost:8000/contracts -H "Content-Type: application/json" -d '{"dataset": "sales", "retention_days": 30}'
	```
- **Signed upload URL:**
	```bash
	curl -X POST http://localhost:8000/datasets/sales/upload-url -H "Content-Type: application/json" -d '{"filename": "sales_2024_01.csv"}'
	```
- **Replay:**
	```bash
	curl -X POST http://localhost:8000/replay -H "Content-Type: application/json" -d '{"dataset": "sales"}'
	```


# lakehouse_fastapi_demo Project (Polylith Example)

This project demonstrates a self-service Lakehouse platform in Polylith style with Orchestrix.

- **FastAPI app:** REST API for dataset registration, contracts, data uploads (signed URL), replay
- **Shell scripts:** curl demos for API
- **Dependency injection:** Components are injected in the project

## Quickstart
- `main.py`: FastAPI server
- `scripts/`: curl demos

## Architecture
- Domain logic & protocols: `bases/orchestrix/lakehouse_fastapi_demo/`
- Infrastructure components: as Python modules in the project
- No changes needed in `components/`!

## Advantages (Orchestrix/Polylith)
- Clear separation of domain, infrastructure, API & demo
- Swappable components (e.g. EventStore, Storage)
- Testability & extensibility
- Readable, traceable architecture

See the README in the base for details on domain and protocols.
