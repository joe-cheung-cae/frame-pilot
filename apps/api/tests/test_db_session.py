from sqlalchemy import create_engine, inspect, text

from app.db.session import _ensure_export_record_columns


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
