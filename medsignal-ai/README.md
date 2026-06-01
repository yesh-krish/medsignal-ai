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
