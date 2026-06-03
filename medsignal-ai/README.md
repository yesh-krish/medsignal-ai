# MedSignal AI

Clean full-stack scaffold for a medication signal application.

## Stack

- Backend: FastAPI, Python, SQLAlchemy, PostgreSQL, Pydantic, httpx
- Frontend: Next.js, TypeScript, Tailwind CSS
- Database: PostgreSQL
- Local dev: Docker Compose

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The app will be available at:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health check: http://localhost:8000/health
- MLflow UI: http://localhost:5000

## Backend

The backend exposes `GET /health`, returning:

```json
{"status": "ok"}
```

Database configuration is read from `DATABASE_URL`. Docker Compose sets it to the
Postgres service URL automatically.

### Migrations

Alembic is configured under `backend/alembic`.

Inside the backend container:

```bash
alembic upgrade head
alembic revision --autogenerate -m "your migration"
```

## Frontend

The frontend reads the backend URL from `NEXT_PUBLIC_BACKEND_URL` and displays
the backend health status on the homepage.

## MLflow Tracking

Docker Compose starts an MLflow tracking server at http://localhost:5000.

Safety summaries generated from FDA label sections are logged to the
`medsignal-label-summarization` experiment. Each run records:

- Parameters: `model_name`, `drug_id`, `normalized_drug_name`
- Metrics: `input_length`, `output_length`, `latency_ms`
- Artifact: `generated_summary.txt`

The backend connects to MLflow through `MLFLOW_TRACKING_URI`. In Docker Compose,
the backend uses `http://mlflow:5000`; from your browser, open the UI at
http://localhost:5000.
