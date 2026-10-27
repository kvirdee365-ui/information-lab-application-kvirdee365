
from pathlib import Path

from src.transform import transform_snapshot


REQUIRED_COLUMNS = [
    "collected_at",
    "line_id",
    "line_name",
    "status_severity",
    "status_description",
    "reason",
]


def validate_dataframe(df):
    """Check basic quality rules for transformed TfL status data."""

    issues = []

    # Check that the expected columns are present.
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]
    if missing_columns:
        issues.append(f"Missing columns: {missing_columns}")

    if df.empty:
        issues.append("The transformed dataset is empty.")
        return issues

    # Check that key identifying fields are populated.
    for column in ["collected_at", "line_id", "line_name"]:
        if column in df.columns and df[column].isna().any():
            issues.append(f"Some records have missing values in '{column}'.")

    # Severity should be numeric when supplied.
    if "status_severity" in df.columns:
        severity = df["status_severity"].dropna()
        if not severity.map(
            lambda value: isinstance(value, (int, float))
        ).all():
            issues.append("Some status severity values are not numeric.")

    return issues


if __name__ == "__main__":
    raw_dir = Path("data/raw")
    snapshots = sorted(raw_dir.glob("tube_status_*.json"))

    if not snapshots:
        raise FileNotFoundError(
            "No raw snapshots found. Run 'python -m src.collect' first."
        )

    df = transform_snapshot(snapshots[-1])
    issues = validate_dataframe(df)

    if issues:
        print("Validation FAILED:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("Validation PASSED.")
        print(f"Checked {len(df)} status records.")
