
from pathlib import Path

from src.collect import collect_tube_status
from src.transform import transform_snapshot
from src.validate import validate_dataframe
from src.compare import compare_snapshots
from src.database import initialise_database, store_observations


def run_pipeline():
    """Run the end-to-end TfL status data pipeline."""

    print("\n=== 1. Collect ===")
    current_snapshot = collect_tube_status()

    print("\n=== 2. Transform ===")
    current_df = transform_snapshot(current_snapshot)
    print(f"Transformed {len(current_df)} status records.")

    print("\n=== 3. Validate ===")
    issues = validate_dataframe(current_df)

    if issues:
        print("Validation FAILED. Data will not be loaded.")
        for issue in issues:
            print(f"- {issue}")
        return False

    print("Validation PASSED.")

    print("\n=== 4. Compare ===")
    raw_dir = Path("data/raw")
    previous_snapshots = sorted(
        path
        for path in raw_dir.glob("tube_status_*.json")
        if path != current_snapshot
    )

    if previous_snapshots:
        previous_snapshot = previous_snapshots[-1]
        previous_df = transform_snapshot(previous_snapshot)

        comparison = compare_snapshots(previous_df, current_df)

        print(f"Previous snapshot: {previous_snapshot.name}")
        print(f"Current snapshot:  {current_snapshot.name}")
        print(comparison.to_string(index=False))
    else:
        print("No previous snapshot available for comparison.")

    print("\n=== 5. Load ===")
    initialise_database()

    rows_stored = store_observations(
        current_df,
        source_snapshot=current_snapshot.name,
    )

    print(f"New observations stored: {rows_stored}")

    print("\n=== Pipeline complete ===")
    return True


if __name__ == "__main__":
    run_pipeline()
