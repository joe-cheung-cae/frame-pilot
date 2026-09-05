import pytest
from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel

from app.core.config import reset_settings_cache
from app.db.migrations import (
    CURRENT_SCHEMA_VERSION,
    UnsupportedSchemaVersionError,
    get_schema_version,
    run_migrations,
    set_schema_version,
)
from app.db.session import (
    SQLITE_BUSY_TIMEOUT_MS,
    _ensure_export_record_columns,
    _ensure_performance_indexes,
    get_engine,
    init_db,
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
    assert "processed_count" in columns
    assert "total_count" in columns
    assert "include_xmp" in columns


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


def test_init_db_runs_versioned_migrations_once(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "migrated"))
    reset_settings_cache()

    init_db()
    engine = get_engine()
    assert get_schema_version(engine) == CURRENT_SCHEMA_VERSION

    init_db()
    assert get_schema_version(engine) == CURRENT_SCHEMA_VERSION


def test_run_migrations_upgrades_legacy_database_without_schema_meta(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy-upgrade.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE project (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    root_path VARCHAR NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    total_images INTEGER NOT NULL,
                    processed_images INTEGER NOT NULL
                )
                """
            )
        )
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

    assert get_schema_version(engine) == 0
    version = run_migrations(engine)
    assert version == CURRENT_SCHEMA_VERSION

    columns = {column["name"] for column in inspect(engine).get_columns("exportrecord")}
    assert "selected_count" in columns
    assert "error_message" in columns
    assert "include_xmp" in columns
    project_columns = {column["name"] for column in inspect(engine).get_columns("project")}
    assert "schema_version" in project_columns
    # create_all may not have created processingjob on this minimal legacy DB; ensure helper path
    # still lands lease columns when the table exists after a fuller migrate.
    if inspect(engine).has_table("processingjob"):
        job_columns = {column["name"] for column in inspect(engine).get_columns("processingjob")}
        assert "worker_id" in job_columns
        assert "heartbeat_at" in job_columns


def test_migrate_to_4_adds_job_lease_columns(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'lease-upgrade.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE processingjob (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    project_id VARCHAR NOT NULL,
                    job_type VARCHAR NOT NULL DEFAULT 'processing',
                    status VARCHAR NOT NULL,
                    current_step VARCHAR NOT NULL,
                    total_items INTEGER NOT NULL,
                    processed_items INTEGER NOT NULL,
                    failed_items INTEGER NOT NULL DEFAULT 0,
                    progress_percent FLOAT NOT NULL DEFAULT 0,
                    error_message VARCHAR,
                    cancellation_requested BOOLEAN NOT NULL DEFAULT 0,
                    cancelled_at DATETIME,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
    set_schema_version(engine, 3)
    assert run_migrations(engine) == CURRENT_SCHEMA_VERSION
    job_columns = {column["name"] for column in inspect(engine).get_columns("processingjob")}
    assert "checkpoint_photo_id" in job_columns
    assert "worker_id" in job_columns
    assert "heartbeat_at" in job_columns
    assert "pause_requested" in job_columns


def test_migrate_to_6_adds_include_xmp_to_existing_export_record(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'xmp-upgrade.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE exportrecord (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    project_id VARCHAR NOT NULL,
                    mode VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    selected_count INTEGER NOT NULL DEFAULT 0,
                    processed_count INTEGER NOT NULL DEFAULT 0,
                    total_count INTEGER NOT NULL DEFAULT 0,
                    statuses VARCHAR NOT NULL DEFAULT '[]',
                    output_path VARCHAR NOT NULL,
                    error_message VARCHAR,
                    completed_at DATETIME,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
    set_schema_version(engine, 5)
    assert "include_xmp" not in {column["name"] for column in inspect(engine).get_columns("exportrecord")}
    assert run_migrations(engine) == CURRENT_SCHEMA_VERSION
    columns = {column["name"] for column in inspect(engine).get_columns("exportrecord")}
    assert "include_xmp" in columns
    assert get_schema_version(engine) == 6


def test_run_migrations_rejects_future_schema_version(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'future.db'}")
    SQLModel.metadata.create_all(engine)
    set_schema_version(engine, CURRENT_SCHEMA_VERSION + 5)

    with pytest.raises(UnsupportedSchemaVersionError, match="newer than this FramePilot build"):
        run_migrations(engine)
