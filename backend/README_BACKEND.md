# LifeLink Backend

## Quick Start

### Prerequisites
1. **MongoDB** must be running on `localhost:27017`
2. **Python 3.10+** installed
3. **Ollama** (optional) for AI features

### Running the Backend

**Option 1: Double-click the batch file**
- Just double-click `run_backend.bat`

**Option 2: PowerShell**
```powershell
.\run_backend_persistent.ps1
```

**Option 3: Direct command**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Accessing the Backend

Once running, access the backend at:

✅ **Correct URLs:**
- API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**
- Health Check: **http://localhost:8000/health**

❌ **Don't use:** `http://0.0.0.0:8000` (this won't work in browsers!)

### API Endpoints

- `GET /health` - Check if backend is running
- `GET /memories/` - List all memories
- `POST /memories/` - Create a new memory
- `PUT /memories/{id}` - Update a memory
- `DELETE /memories/{id}` - Delete a memory

### Troubleshooting

1. **"MongoDB is not running"**
   - Start MongoDB: `mongod`

2. **"Can't reach 0.0.0.0:8000"**
   - Use `http://localhost:8000` instead!

3. **Port already in use**
   - Kill existing process or change port in `config.py`

### Frontend Connection

The frontend should connect to `http://localhost:8000` (not `0.0.0.0:8000`).
