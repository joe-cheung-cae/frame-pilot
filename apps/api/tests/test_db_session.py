from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel

from app.core.config import reset_settings_cache
from app.db.session import (
    SQLITE_BUSY_TIMEOUT_MS,
    _ensure_export_record_columns,
    _ensure_performance_indexes,
    get_engine,
    reset_engine_cache,
)
from app.models.entities import ExportRecord, Photo, PhotoGroup, ProcessingJob, Project  # noqa: F401


def test_init_db_adds_missing_export_record_columns_to_existing_sqlite_table(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE exportrecord (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    project_id VARCHAR NOT NULL,
                    mode VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    output_path VARCHAR NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )

    _ensure_export_record_columns(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("exportrecord")}
    assert "selected_count" in columns
    assert "statuses" in columns
    assert "error_message" in columns
    assert "completed_at" in columns


def test_init_db_adds_large_project_query_indexes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'indexes.db'}")
    SQLModel.metadata.create_all(engine)

    _ensure_performance_indexes(engine)
    _ensure_performance_indexes(engine)

    inspector = inspect(engine)
    photo_indexes = {index["name"] for index in inspector.get_indexes("photo")}
    group_indexes = {index["name"] for index in inspector.get_indexes("photogroup")}
    job_indexes = {index["name"] for index in inspector.get_indexes("processingjob")}
    export_indexes = {index["name"] for index in inspector.get_indexes("exportrecord")}

    assert "ix_photo_project_review_order" in photo_indexes
    assert "ix_photo_project_status_filename" in photo_indexes
    assert "ix_photo_project_processing_state" in photo_indexes
    assert "ix_photogroup_project_created" in group_indexes
    assert "ix_processingjob_project_active" in job_indexes
    assert "ix_processingjob_project_created" in job_indexes
    assert "ix_exportrecord_project_created" in export_indexes


def test_get_engine_reuses_cached_engine_for_same_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "shared"))
    reset_settings_cache()

    first = get_engine()
    second = get_engine()
    assert first is second

    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "other"))
    reset_settings_cache()
    third = get_engine()
    assert third is not first

    reset_engine_cache()
    fourth = get_engine()
    assert fourth is not third


def test_get_engine_applies_wal_and_busy_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "wal"))
    reset_settings_cache()

    engine = get_engine()
    with engine.connect() as connection:
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar()
        busy_timeout = connection.execute(text("PRAGMA busy_timeout")).scalar()
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar()

    assert str(journal_mode).lower() == "wal"
    assert int(busy_timeout) == SQLITE_BUSY_TIMEOUT_MS
    assert int(foreign_keys) == 1
