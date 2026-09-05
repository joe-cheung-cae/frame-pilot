"""Versioned SQLite schema migrations for FramePilot local databases."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import inspect, text

from app.db import session as db_session

CURRENT_SCHEMA_VERSION = 5


class UnsupportedSchemaVersionError(RuntimeError):
    """Raised when the on-disk schema is newer than this code build."""


def _ensure_schema_meta_table(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    id INTEGER NOT NULL PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL
                )
                """
            )
        )


def get_schema_version(engine) -> int:
    _ensure_schema_meta_table(engine)
    with engine.connect() as connection:
        row = connection.execute(text("SELECT version FROM schema_meta WHERE id = 1")).first()
    return int(row[0]) if row is not None else 0


def set_schema_version(engine, version: int) -> None:
    _ensure_schema_meta_table(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schema_meta (id, version) VALUES (1, :version)
                ON CONFLICT(id) DO UPDATE SET version = excluded.version
                """
            ),
            {"version": version},
        )


def _migrate_to_1(engine) -> None:
    """Bring pre-runner local databases up to the current column/index baseline."""
    db_session._ensure_project_columns(engine)
    db_session._ensure_export_record_columns(engine)
    db_session._ensure_photo_group_columns(engine)
    db_session._ensure_photo_columns(engine)
    db_session._ensure_processing_job_columns(engine)
    db_session._ensure_performance_indexes(engine)


def _migrate_to_2(engine) -> None:
    """Add stable PhotoGroup.sequence for capture-time review ordering."""
    db_session._ensure_photo_group_columns(engine)
    inspector = inspect(engine)
    if not inspector.has_table("photogroup"):
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE photogroup
                SET sequence = (
                    SELECT COUNT(*)
                    FROM photogroup AS earlier
                    WHERE earlier.project_id = photogroup.project_id
                      AND (
                        earlier.created_at < photogroup.created_at
                        OR (earlier.created_at = photogroup.created_at AND earlier.id <= photogroup.id)
                      )
                )
                WHERE sequence = 0
                """
            )
        )


def _migrate_to_3(engine) -> None:
    """Add ExportRecord processed/total progress counters for running exports."""
    db_session._ensure_export_record_columns(engine)
    inspector = inspect(engine)
    if not inspector.has_table("exportrecord"):
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE exportrecord
                SET total_count = selected_count
                WHERE total_count = 0 AND selected_count > 0
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE exportrecord
                SET processed_count = selected_count
                WHERE status = 'complete' AND processed_count = 0 AND selected_count > 0
                """
            )
        )


def _migrate_to_4(engine) -> None:
    """Add Phase 6 durable job checkpoint and lease columns on ProcessingJob."""
    db_session._ensure_processing_job_columns(engine)


def _migrate_to_5(engine) -> None:
    """Add cooperative processing pause_requested on ProcessingJob (S9.02 / J7.07)."""
    db_session._ensure_processing_job_columns(engine)


MIGRATIONS: dict[int, Callable] = {
    1: _migrate_to_1,
    2: _migrate_to_2,
    3: _migrate_to_3,
    4: _migrate_to_4,
    5: _migrate_to_5,
}


def run_migrations(engine) -> int:
    """Apply pending migrations and return the resulting schema version."""
    _ensure_schema_meta_table(engine)
    current = get_schema_version(engine)
    if current > CURRENT_SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"Database schema version {current} is newer than this FramePilot build "
            f"(supports up to {CURRENT_SCHEMA_VERSION}). Upgrade the application before opening this database."
        )

    for version in range(current + 1, CURRENT_SCHEMA_VERSION + 1):
        migrate = MIGRATIONS.get(version)
        if migrate is None:
            raise RuntimeError(f"Missing migration implementation for schema version {version}")
        migrate(engine)
        set_schema_version(engine, version)

    return get_schema_version(engine)


def schema_meta_exists(engine) -> bool:
    return inspect(engine).has_table("schema_meta")
