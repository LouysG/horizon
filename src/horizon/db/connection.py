"""Open and initialize Horizon's embedded DuckDB database."""

from pathlib import Path

import duckdb

# Locate the database and schema used by the default connection.
DEFAULT_DATABASE_PATH = Path("data/horizon.duckdb")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> duckdb.DuckDBPyConnection:
    """Open a database file and initialize its schema if needed.

    The default path is relative to the current directory. Run from the project
    root or pass an explicit path when running elsewhere.
    """

    # Create the parent directory before opening the database.
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Open the database and configure spatial and temporal conventions.
    connection = duckdb.connect(str(path))
    try:
        connection.execute(query="INSTALL AND LOAD spatial")
        connection.execute(query="SET geometry_always_xy = true")
        connection.execute(query="SET TimeZone = 'UTC'")

        # Create the schema objects on first use.
        connection.execute(query=SCHEMA_PATH.read_text(encoding="utf-8"))
    except BaseException:
        # Release the connection if setup fails.
        connection.close()
        raise

    # Hand the initialized connection to the caller.
    return connection
