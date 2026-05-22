# GangaRakshak AI Backend

Lightweight FastAPI incident backend for Phase 6 prototype persistence.

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your Neon PostgreSQL connection string.
4. Run the API:

```bash
uvicorn app.main:app --reload
```

The API starts on `http://localhost:8000` and serves incident routes at `http://localhost:8000/api/incidents`.

For local frontend development, allow both common Next.js ports:

```bash
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

## Frontend

Use these frontend environment variables:

```bash
NEXT_PUBLIC_USE_INCIDENT_BACKEND=true
NEXT_PUBLIC_INCIDENT_API_BASE_URL=http://localhost:8000/api
```
# ganga-backend
