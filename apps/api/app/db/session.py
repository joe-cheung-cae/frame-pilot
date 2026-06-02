from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


def get_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False}
    return create_engine(settings.database_url, connect_args=connect_args)


def init_db() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _ensure_export_record_columns(engine)


def _ensure_export_record_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("exportrecord"):
        return

    existing = {column["name"] for column in inspector.get_columns("exportrecord")}
    statements = []
    if "selected_count" not in existing:
        statements.append("ALTER TABLE exportrecord ADD COLUMN selected_count INTEGER NOT NULL DEFAULT 0")
    if "statuses" not in existing:
        statements.append("ALTER TABLE exportrecord ADD COLUMN statuses VARCHAR NOT NULL DEFAULT '[]'")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
