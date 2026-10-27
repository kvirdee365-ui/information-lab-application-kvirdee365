
from pathlib import Path

from src.database import initialise_database, store_observations
from src.transform import transform_snapshot


def load_latest_snapshot():
    """Transform and load the latest snapshot only once."""

    raw_dir = Path("data/raw")
    snapshots = sorted(raw_dir.glob("tube_status_*.json"))

    if not snapshots:
        raise FileNotFoundError(
            "No raw snapshots found. Run 'python -m src.collect' first."
        )

    latest_snapshot = snapshots[-1]
    observations = transform_snapshot(latest_snapshot)

    initialise_database()

    rows_stored = store_observations(
        observations,
        source_snapshot=latest_snapshot.name,
    )

    print(f"Source snapshot: {latest_snapshot.name}")
    print(f"Observations stored: {rows_stored}")


if __name__ == "__main__":
    load_latest_snapshot()
