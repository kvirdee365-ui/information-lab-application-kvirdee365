
from pathlib import Path

import duckdb
import pandas as pd


DEFAULT_DB_PATH = Path("data/tfl_status.duckdb")


def initialise_database(db_path=DEFAULT_DB_PATH):
    """Create the database tables if they do not already exist."""

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(db_path)) as connection:
        connection.execute("""
            CREATE SEQUENCE IF NOT EXISTS observation_id_sequence
            START 1
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS status_observations (
                id BIGINT PRIMARY KEY,
                collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
                line_id VARCHAR NOT NULL,
                line_name VARCHAR NOT NULL,
                status_severity INTEGER,
                status_description VARCHAR,
                reason VARCHAR
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS processed_snapshots (
                source_snapshot VARCHAR PRIMARY KEY,
                loaded_at TIMESTAMP WITH TIME ZONE
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)


def store_observations(
    df,
    db_path=DEFAULT_DB_PATH,
    source_snapshot=None,
):
    """Store observations, skipping snapshots already processed."""

    required_columns = [
        "collected_at",
        "line_id",
        "line_name",
        "status_severity",
        "status_description",
        "reason",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df.empty:
        raise ValueError("Cannot store an empty observations dataset.")

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    records = df[required_columns].copy()
    records["collected_at"] = pd.to_datetime(
        records["collected_at"], utc=True
    )
    records = records.astype(object).where(pd.notna(records), None)

    with duckdb.connect(str(db_path)) as connection:
        connection.execute("BEGIN TRANSACTION")

        try:
            if source_snapshot is not None:
                already_loaded = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM processed_snapshots
                    WHERE source_snapshot = ?
                    """,
                    [source_snapshot],
                ).fetchone()[0]

                if already_loaded:
                    connection.execute("COMMIT")
                    print(f"Snapshot already loaded: {source_snapshot}")
                    return 0

            for row in records.itertuples(index=False, name=None):
                connection.execute(
                    """
                    INSERT INTO status_observations (
                        id, collected_at, line_id, line_name,
                        status_severity, status_description, reason
                    )
                    VALUES (
                        nextval('observation_id_sequence'),
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    row,
                )

            if source_snapshot is not None:
                connection.execute(
                    """
                    INSERT INTO processed_snapshots (source_snapshot)
                    VALUES (?)
                    """,
                    [source_snapshot],
                )

            connection.execute("COMMIT")

        except Exception:
            connection.execute("ROLLBACK")
            raise

    return len(records)


def load_observations(db_path=DEFAULT_DB_PATH):
    """Load historical observations into a pandas DataFrame."""

    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}. "
            "Initialise the database and store observations first."
        )

    with duckdb.connect(str(db_path), read_only=True) as connection:
        return connection.execute("""
            SELECT
                collected_at,
                line_id,
                line_name,
                status_severity,
                status_description,
                reason
            FROM status_observations
            ORDER BY collected_at, line_id
        """).df()


if __name__ == "__main__":
    initialise_database()
    print(f"Database initialised at: {DEFAULT_DB_PATH}")
