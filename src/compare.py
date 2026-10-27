
from pathlib import Path

import pandas as pd

from src.transform import transform_snapshot


REQUIRED_COLUMNS = [
    "line_id",
    "line_name",
    "status_description",
    "reason",
]


def consolidate_lines(df):
    """Combine multiple status records into one record per Tube line."""

    # Ensure empty DataFrames still have the columns we need.
    df = df.reindex(columns=REQUIRED_COLUMNS)

    def combine_unique(values):
        """Combine distinct, non-empty values into a readable string."""
        unique_values = []

        for value in values:
            if pd.isna(value):
                continue

            value = str(value).strip()

            if value and value not in unique_values:
                unique_values.append(value)

        return " | ".join(unique_values) if unique_values else None

    return (
        df.groupby("line_id", dropna=False, as_index=False)
        .agg(
            line_name=("line_name", "first"),
            status_description=("status_description", combine_unique),
            reason=("reason", combine_unique),
        )
    )


def compare_snapshots(previous_df, current_df):
    """Compare reported Tube statuses and reasons between observations."""

    previous = consolidate_lines(previous_df).rename(
        columns={
            "line_name": "line_name_previous",
            "status_description": "previous_status",
            "reason": "previous_reason",
        }
    )

    current = consolidate_lines(current_df).rename(
        columns={
            "line_name": "line_name_current",
            "status_description": "current_status",
            "reason": "current_reason",
        }
    )

    comparison = previous.merge(
        current,
        on="line_id",
        how="outer",
        indicator=True,
        validate="one_to_one",
    )

    comparison["line_name"] = comparison[
        "line_name_current"
    ].combine_first(comparison["line_name_previous"])

    comparison["change_type"] = comparison["_merge"].map({
        "left_only": "Missing from current snapshot",
        "right_only": "New in current snapshot",
        "both": "Unchanged",
    }).astype("object")

    both = comparison["_merge"] == "both"

    previous_status = comparison["previous_status"].astype("string").fillna("")
    current_status = comparison["current_status"].astype("string").fillna("")
    previous_reason = comparison["previous_reason"].astype("string").fillna("")
    current_reason = comparison["current_reason"].astype("string").fillna("")

    status_changed = previous_status != current_status
    reason_changed = previous_reason != current_reason

    comparison.loc[
        both & reason_changed & ~status_changed,
        "change_type",
    ] = "Reason changed"

    comparison.loc[
        both & status_changed,
        "change_type",
    ] = "Status changed"

    became_disrupted = (
        both
        & previous_status.str.casefold().eq("good service")
        & ~current_status.str.casefold().eq("good service")
        & status_changed
    )
    comparison.loc[
        became_disrupted, "change_type"
    ] = "Changed from Good Service"

    improved = (
        both
        & ~previous_status.str.casefold().eq("good service")
        & current_status.str.casefold().eq("good service")
        & status_changed
    )
    comparison.loc[
        improved, "change_type"
    ] = "Changed to Good Service"

    return (
        comparison[
            [
                "line_id",
                "line_name",
                "previous_status",
                "current_status",
                "previous_reason",
                "current_reason",
                "change_type",
            ]
        ]
        .sort_values("line_name", na_position="last")
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    raw_dir = Path("data/raw")
    snapshots = sorted(raw_dir.glob("tube_status_*.json"))

    if len(snapshots) < 2:
        raise FileNotFoundError(
            "At least two snapshots are required. "
            "Run 'python -m src.collect' twice, with a pause between runs."
        )

    previous_df = transform_snapshot(snapshots[-2])
    current_df = transform_snapshot(snapshots[-1])

    result = compare_snapshots(previous_df, current_df)

    print("Comparison of reported Tube statuses")
    print(f"Previous snapshot: {snapshots[-2].name}")
    print(f"Current snapshot:  {snapshots[-1].name}\n")
    print(result.to_string(index=False))
