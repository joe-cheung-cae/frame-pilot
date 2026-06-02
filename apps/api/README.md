# FramePilot API

Local FastAPI backend for FramePilot. It stores metadata in SQLite under `FRAMEPILOT_DATA_DIR` or `.framepilot-data` by default.

Run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e 'apps/api[dev]'
npm run dev:api
```
