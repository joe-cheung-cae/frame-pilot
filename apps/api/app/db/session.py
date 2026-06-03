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
    _ensure_project_columns(engine)
    _ensure_export_record_columns(engine)
    _ensure_photo_group_columns(engine)
    _ensure_photo_columns(engine)
    _ensure_processing_job_columns(engine)
    _ensure_performance_indexes(engine)


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

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
