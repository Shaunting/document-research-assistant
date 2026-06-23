# Backend

FastAPI service for Document Copilot. Python 3.12+, managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
cd backend
uv sync
cp .env.example .env   # fill in Supabase + OpenAI values
```

See [docs/guides/supabase-setup.md](../docs/guides/supabase-setup.md) for credentials.

## Run

```bash
uv run uvicorn app.main:app --reload
```

Health check: http://localhost:8000/health

Alternative: `uv run python app/main.py`

## Tests & lint

```bash
uv run pytest -m "not integration"
uv run ruff check .
```

## Migrations

Use the direct Supabase database URL (not the pooler). From `backend/`:

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"   # review before applying
```

More detail: [docs/guides/backend-setup.md](../docs/guides/backend-setup.md)
