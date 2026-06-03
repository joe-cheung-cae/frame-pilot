from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel

from app.db.session import _ensure_export_record_columns, _ensure_performance_indexes
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

    assert "ix_photo_project_review_order" in photo_indexes
    assert "ix_photo_project_status_filename" in photo_indexes
    assert "ix_photogroup_project_created" in group_indexes
    assert "ix_processingjob_project_active" in job_indexes
