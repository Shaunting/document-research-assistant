from sqlalchemy import Engine, create_engine

from app.config import settings


def get_engine() -> Engine:
    """Create a new `Engine` (and its own connection pool) on every call.

    This does not return a cached/shared engine -- callers should call this
    once and reuse the returned `Engine`, not call it repeatedly in a hot
    path (each call opens a fresh pool).
    """
    db_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(db_url)
