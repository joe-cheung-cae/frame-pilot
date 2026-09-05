from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import event, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

SQLITE_BUSY_TIMEOUT_MS = 5000


def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    cursor.close()


@lru_cache
def _engine_for_url(database_url: str):
    connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, connect_args=connect_args)
    event.listen(engine, "connect", _configure_sqlite_connection)
    return engine


def get_engine():
    settings = get_settings()
    return _engine_for_url(settings.database_url)


def reset_engine_cache() -> None:
    _engine_for_url.cache_clear()


def init_db() -> None:
    from app.db.migrations import run_migrations

    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    run_migrations(engine)
    _ensure_processing_job_columns(engine)


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
    if "error_message" not in existing:
        statements.append("ALTER TABLE exportrecord ADD COLUMN error_message VARCHAR")
    if "completed_at" not in existing:
        statements.append("ALTER TABLE exportrecord ADD COLUMN completed_at DATETIME")
    if "processed_count" not in existing:
        statements.append("ALTER TABLE exportrecord ADD COLUMN processed_count INTEGER NOT NULL DEFAULT 0")
    if "total_count" not in existing:
        statements.append("ALTER TABLE exportrecord ADD COLUMN total_count INTEGER NOT NULL DEFAULT 0")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_project_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("project"):
        return

    existing = {column["name"] for column in inspector.get_columns("project")}
    statements = []
    if "source_mode" not in existing:
        statements.append("ALTER TABLE project ADD COLUMN source_mode VARCHAR NOT NULL DEFAULT 'copy'")
    if "source_root_path" not in existing:
        statements.append("ALTER TABLE project ADD COLUMN source_root_path VARCHAR")
    if "last_processed_at" not in existing:
        statements.append("ALTER TABLE project ADD COLUMN last_processed_at DATETIME")
    if "schema_version" not in existing:
        statements.append("ALTER TABLE project ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 2")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_photo_group_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("photogroup"):
        return

    existing = {column["name"] for column in inspector.get_columns("photogroup")}
    statements = []
    if "score_summary" not in existing:
        statements.append("ALTER TABLE photogroup ADD COLUMN score_summary VARCHAR NOT NULL DEFAULT '{}'")
    if "sequence" not in existing:
        statements.append("ALTER TABLE photogroup ADD COLUMN sequence INTEGER NOT NULL DEFAULT 0")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_photo_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("photo"):
        return

    existing = {column["name"] for column in inspector.get_columns("photo")}
    statements = []
    if "project_copy_path" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN project_copy_path VARCHAR")
    if "source_identity" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN source_identity VARCHAR")
    if "file_ext" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN file_ext VARCHAR")
    if "file_mtime" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN file_mtime FLOAT")
    if "content_hash" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN content_hash VARCHAR")
    if "perceptual_hash" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN perceptual_hash VARCHAR")
    if "processing_state" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN processing_state VARCHAR NOT NULL DEFAULT 'imported'")
    if "processing_error" not in existing:
        statements.append("ALTER TABLE photo ADD COLUMN processing_error VARCHAR")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_processing_job_columns(engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("processingjob"):
        return

    existing = {column["name"] for column in inspector.get_columns("processingjob")}
    statements = []
    if "job_type" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN job_type VARCHAR NOT NULL DEFAULT 'processing'")
    if "failed_items" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN failed_items INTEGER NOT NULL DEFAULT 0")
    if "progress_percent" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN progress_percent FLOAT NOT NULL DEFAULT 0")
    if "cancellation_requested" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0")
    if "pause_requested" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN pause_requested BOOLEAN NOT NULL DEFAULT 0")
    if "cancelled_at" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN cancelled_at DATETIME")
    if "checkpoint_photo_id" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN checkpoint_photo_id VARCHAR")
    if "checkpoint_stage" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN checkpoint_stage VARCHAR")
    if "interrupted_at" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN interrupted_at DATETIME")
    if "reclaim_count" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN reclaim_count INTEGER NOT NULL DEFAULT 0")
    if "worker_id" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN worker_id VARCHAR")
    if "heartbeat_at" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN heartbeat_at DATETIME")
    if "started_at" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN started_at DATETIME")
    if "completed_at" not in existing:
        statements.append("ALTER TABLE processingjob ADD COLUMN completed_at DATETIME")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_performance_indexes(engine) -> None:
    inspector = inspect(engine)
    statements = []

    if inspector.has_table("photo"):
        photo_indexes = {index["name"] for index in inspector.get_indexes("photo")}
        if "ix_photo_project_review_order" not in photo_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_photo_project_review_order
                ON photo (project_id, group_id, ai_recommendation, overall_score, filename)
                """
            )
        if "ix_photo_project_status_filename" not in photo_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_photo_project_status_filename
                ON photo (project_id, user_status, filename)
                """
            )
        if "ix_photo_project_processing_state" not in photo_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_photo_project_processing_state
                ON photo (project_id, processing_state)
                """
            )

    if inspector.has_table("photogroup"):
        group_indexes = {index["name"] for index in inspector.get_indexes("photogroup")}
        if "ix_photogroup_project_created" not in group_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_photogroup_project_created
                ON photogroup (project_id, created_at, id)
                """
            )

    if inspector.has_table("processingjob"):
        job_indexes = {index["name"] for index in inspector.get_indexes("processingjob")}
        if "ix_processingjob_project_active" not in job_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_processingjob_project_active
                ON processingjob (project_id, job_type, status, created_at, id)
                """
            )
        if "ix_processingjob_project_created" not in job_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_processingjob_project_created
                ON processingjob (project_id, created_at, id)
                """
            )

    if inspector.has_table("exportrecord"):
        export_indexes = {index["name"] for index in inspector.get_indexes("exportrecord")}
        if "ix_exportrecord_project_created" not in export_indexes:
            statements.append(
                """
                CREATE INDEX IF NOT EXISTS ix_exportrecord_project_created
                ON exportrecord (project_id, created_at, id)
                """
            )

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
