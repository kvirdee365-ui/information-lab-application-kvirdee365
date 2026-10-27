
import json
from pathlib import Path

import pandas as pd


def transform_snapshot(snapshot_path):
    """Convert a saved raw TfL snapshot into a structured DataFrame."""

    snapshot_path = Path(snapshot_path)

    with snapshot_path.open("r", encoding="utf-8") as file:
        snapshot = json.load(file)

    collected_at = snapshot["collected_at"]
    records = []

    for line in snapshot["data"]:
        statuses = line.get("lineStatuses", [])

        # Some lines may not have status entries, so handle that case.
        if not statuses:
            statuses = [{}]

        for status in statuses:
            records.append({
                "collected_at": collected_at,
                "line_id": line.get("id"),
                "line_name": line.get("name"),
                "status_severity": status.get("statusSeverity"),
                "status_description": status.get(
                    "statusSeverityDescription"
                ),
                "reason": status.get("reason"),
            })

    columns = [
        "collected_at",
        "line_id",
        "line_name",
        "status_severity",
        "status_description",
        "reason",
    ]

    return pd.DataFrame(records, columns=columns)


if __name__ == "__main__":
    raw_dir = Path("data/raw")
    snapshots = sorted(raw_dir.glob("tube_status_*.json"))

    if not snapshots:
        raise FileNotFoundError(
            "No raw snapshots found. Run 'python -m src.collect' first."
        )

    df = transform_snapshot(snapshots[-1])

    print(f"Transformed {len(df)} status records.\n")
    print(df.to_string(index=False))
