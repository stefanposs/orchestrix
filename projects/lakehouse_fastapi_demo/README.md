## Lakehouse Fastapi Demo

### Start the server (recommended):

```bash
uv run uvicorn orchestrix.lakehouse_fastapi_demo.app:app --reload
```

**Alternative:**

With Bash script (e.g. for demo/onboarding):
```bash
bash run_fastapi.sh
```

The script uses the recommended start parameters and works from anywhere in the workspace.

### Example requests & demos

See all HTTP demo scripts and example requests in the folder:
`http_requests/`

Some examples:

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

More demo workflows and sample CSV files can be found in `http_requests/`.