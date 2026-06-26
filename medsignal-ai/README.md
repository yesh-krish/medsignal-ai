# MedSignal AI

MedSignal AI is a full-stack medication safety intelligence project. It lets a
user search for a medication, view RxNorm-normalized drug identity data, inspect
openFDA reported adverse event trends, read FDA label sections, generate a
plain-English AI safety summary, and track summarizer runs with MLflow.

This project is designed as a software engineering portfolio piece: clean API
boundaries, typed frontend data contracts, Dockerized local development,
database migrations, tests, and lightweight data pipelines.

## Problem Statement

Medication safety data is spread across multiple public sources and is difficult
to explore quickly. MedSignal AI brings several signals into one local dashboard:

- RxNorm drug normalization
- openFDA reported adverse events
- openFDA drug label sections
- AI-generated label summaries
- MLflow experiment tracking
- Prefect refresh and signal detection flows

The app uses careful wording throughout: it shows **reported adverse events** and
**potential safety signals**. It does not claim that a medication causes an
event or that an alert is a confirmed drug risk.

## Tech Stack

- Backend: FastAPI, Python, SQLAlchemy, Pydantic, httpx
- Database: PostgreSQL with Alembic migrations
- Frontend: Next.js, TypeScript, Tailwind CSS, Recharts
- AI: Hugging Face Transformers
- Experiment tracking: MLflow
- Pipelines: Prefect
- Local development: Docker Compose
- Tests: pytest

## Architecture

```text
Browser
  |
  v
Next.js frontend :3000
  |
  | NEXT_PUBLIC_BACKEND_URL
  v
FastAPI backend :8000
  |
  |-- RxNorm API
  |-- openFDA adverse event API
  |-- openFDA drug label API
  |-- Hugging Face summarizer
  |-- MLflow tracking server :5000
  |
  v
PostgreSQL :5432

Prefect flows run inside the backend container:
  refresh_drug_data -> refreshes openFDA data and labels
  detect_safety_signals -> saves potential safety signal alerts
```

## Local Setup

Prerequisites:

- Docker Desktop
- Git

Start the app:

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Portfolio: http://localhost:3000
- MedSignal app: http://localhost:3000/medsignal-ai
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health
- MLflow UI: http://localhost:5000

The backend container runs Alembic migrations automatically on startup.

Seed example drugs:

```bash
docker compose exec backend python -m app.scripts.seed_drugs
```

Seeded drugs:

- acetaminophen
- ibuprofen
- metformin
- atorvastatin

## API Routes

```text
GET  /health
GET  /api/drugs/search?query={query}
GET  /api/drugs/{drug_id}
GET  /api/drugs/{drug_id}/events
GET  /api/drugs/{drug_id}/ingestion-runs/latest
GET  /api/drugs/{drug_id}/event-trends
GET  /api/drugs/{drug_id}/label
POST /api/drugs/{drug_id}/summarize-label
GET  /api/drugs/{drug_id}/alerts
POST /api/drugs/{drug_id}/signals/analyze
GET  /api/drugs/{drug_id}/signals/latest
GET  /api/drugs/{drug_id}/signals/history
```

Key behavior:

- Drug search normalizes input through RxNorm and saves/updates the drug.
- Event routes fetch and summarize openFDA reported adverse events.
- Event ingestion paginates openFDA results, keeps the latest case version per
  safety report, and records an auditable ingestion run.
- Label routes fetch FDA label sections when available.
- Summary route generates an educational AI safety summary and logs it to
  MLflow.
- Alerts route returns saved potential safety signals from the Prefect detection
  flow.

## MLflow Usage

Docker Compose starts an MLflow tracking server at http://localhost:5000.

The backend writes summarizer runs to the
`medsignal-label-summarization` experiment. Each run logs:

- Parameters: `model_name`, `drug_id`, `normalized_drug_name`
- Metrics: `input_length`, `output_length`, `latency_ms`
- Artifact: `generated_summary.txt`

Inside Docker Compose, the backend uses:

```text
MLFLOW_TRACKING_URI=http://mlflow:5000
```

## Prefect Usage

Run the refresh flow:

```bash
docker compose exec backend python -m app.pipelines.refresh_drug_data
```

Run potential safety signal detection:

```bash
docker compose exec backend python -m app.pipelines.detect_safety_signals
```

The refresh flow loads saved drugs from PostgreSQL, refreshes openFDA reported
adverse event data, refreshes FDA label data, and logs success or failure per
drug.

Each event refresh records its source query, requested and fetched report counts,
deduplication count, saved reaction rows, source update date, timestamps, and
failure details in `ingestion_runs`. The latest run is displayed in the
dashboard's Data provenance panel.

The signal detection flow compares recent reported adverse event counts with
historical baseline counts. Large increases are saved to `safety_alerts` as
potential safety signals for review.

The PRR/ROR analysis compares reaction reporting for a medication against all
other openFDA FAERS reports. Each immutable analysis run stores its thresholds,
contingency-table counts, PRR, ROR, 95% ROR confidence interval, flag decision,
and plain-English explanation. Run it for every saved medication with:

```bash
docker compose exec backend python -m app.pipelines.analyze_safety_signals
```

The calculations are screening tools for potential safety signals and do not
establish causality or confirmed drug risks.

## Continuous Integration

GitHub Actions runs the backend pytest suite and frontend production build for
pull requests and pushes to `main`.

## Testing

Run backend tests:

```bash
docker compose exec backend pytest
```

Run a frontend production build:

```bash
docker compose exec frontend npm run build
```

## Screenshots

Add screenshots here when preparing the portfolio submission:

- Homepage search and backend health
- Medication dashboard overview
- Reported adverse event charts
- FDA label sections
- AI safety summary card
- MLflow experiment run

## Environment Variables

Use `.env.example` as the local template. The values are development defaults
and do not include production secrets.

Important variables:

- `DOCKER_DATABASE_URL`
- `DATABASE_URL`
- `NEXT_PUBLIC_BACKEND_URL`
- `RXNORM_BASE_URL`
- `OPENFDA_BASE_URL`
- `DOCKER_MLFLOW_TRACKING_URI`
- `MLFLOW_TRACKING_URI`
- `MLFLOW_EXPERIMENT_NAME`
- `SUMMARIZER_MODEL_NAME`

## Safety Disclaimer

MedSignal AI is for educational and engineering demonstration purposes only.
openFDA reports are voluntary and observational; they may contain duplicates,
incomplete information, reporting bias, or events unrelated to the medication.

The dashboard shows reported adverse events and potential safety signals. It
does not diagnose, provide medical advice, confirm adverse reactions, or prove
that a medication causes an event. Always consult a qualified healthcare
professional for medical decisions.
