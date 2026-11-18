"""Open and initialize Horizon's embedded DuckDB database."""

from pathlib import Path

import duckdb

DEFAULT_DATABASE_PATH = Path("data/horizon.duckdb")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> duckdb.DuckDBPyConnection:
    """Open a database file and initialize its schema if needed.

    The default path is relative to the current directory. Run from the project
    root or pass an explicit path when running elsewhere.
    """
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(path))
    try:
        connection.execute(query="INSTALL AND LOAD spatial")
        connection.execute(query="SET geometry_always_xy = true")
        connection.execute(query="SET TimeZone = 'UTC'")
        connection.execute(query=SCHEMA_PATH.read_text(encoding="utf-8"))
    except BaseException:
        connection.close()
        raise

    return connection
