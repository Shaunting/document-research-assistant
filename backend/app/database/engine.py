from sqlalchemy import Engine, create_engine

from app.config import settings


def get_engine() -> Engine:
    db_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(db_url)
