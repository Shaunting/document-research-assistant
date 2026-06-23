# Tests

Run from the `backend/` directory:

```bash
uv run pytest
```

Run a specific file:

```bash
uv run pytest tests/database/models/test_models.py -v
```

## Structure

```
tests/
└── database/
    └── models/
        └── test_models.py   # Structural tests for all SQLAlchemy models
```

## Test types

**Structural (no DB required):** Tests in `tests/database/models/` inspect SQLAlchemy model definitions — column names, types, foreign keys, computed columns. They run without a database connection.

**Integration (requires DB):** Not yet written. Will be marked `@pytest.mark.integration` and require `DATABASE_URL` in the environment.
