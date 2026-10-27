
import pandas as pd

from src.compare import compare_snapshots



def make_snapshot(statuses):
    """Create a small test dataset from line names and statuses."""
    columns = ["line_id", "line_name", "status_description"]

    return pd.DataFrame(
        [
            {
                "line_id": line_id,
                "line_name": line_name,
                "status_description": status,
            }
            for line_id, line_name, status in statuses
        ],
        columns=columns,
    )



def test_good_service_changes_to_disruption():
    previous = make_snapshot([
        ("bakerloo", "Bakerloo", "Good Service"),
    ])
    current = make_snapshot([
        ("bakerloo", "Bakerloo", "Severe Delays"),
    ])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "Changed from Good Service"


def test_disruption_changes_to_good_service():
    previous = make_snapshot([
        ("bakerloo", "Bakerloo", "Severe Delays"),
    ])
    current = make_snapshot([
        ("bakerloo", "Bakerloo", "Good Service"),
    ])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "Changed to Good Service"


def test_unchanged_status_is_detected():
    previous = make_snapshot([
        ("central", "Central", "Good Service"),
    ])
    current = make_snapshot([
        ("central", "Central", "Good Service"),
    ])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "Unchanged"


def test_other_status_change_is_detected():
    previous = make_snapshot([
        ("circle", "Circle", "Part Closure"),
    ])
    current = make_snapshot([
        ("circle", "Circle", "Severe Delays"),
    ])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "Status changed"


def test_line_missing_from_current_snapshot_is_detected():
    previous = make_snapshot([
        ("victoria", "Victoria", "Good Service"),
    ])
    current = make_snapshot([])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "Missing from current snapshot"


def test_new_line_in_current_snapshot_is_detected():
    previous = make_snapshot([])
    current = make_snapshot([
        ("jubilee", "Jubilee", "Good Service"),
    ])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "New in current snapshot"

def test_reason_change_is_detected():
    previous = pd.DataFrame([
        {
            "line_id": "bakerloo",
            "line_name": "Bakerloo",
            "status_description": "Severe Delays",
            "reason": "Earlier signal failure",
        }
    ])

    current = pd.DataFrame([
        {
            "line_id": "bakerloo",
            "line_name": "Bakerloo",
            "status_description": "Severe Delays",
            "reason": "Earlier obstruction on the track",
        }
    ])

    result = compare_snapshots(previous, current)

    assert result.loc[0, "change_type"] == "Reason changed"


def test_multiple_records_for_one_line_are_consolidated():
    previous = pd.DataFrame([
        {
            "line_id": "circle",
            "line_name": "Circle",
            "status_description": "Part Closure",
            "reason": "Closure near Edgware Road",
        },
        {
            "line_id": "circle",
            "line_name": "Circle",
            "status_description": "Part Closure",
            "reason": "Closure near Tower Hill",
        },
    ])

    current = pd.DataFrame([
        {
            "line_id": "circle",
            "line_name": "Circle",
            "status_description": "Part Closure",
            "reason": "Closure near Edgware Road",
        },
        {
            "line_id": "circle",
            "line_name": "Circle",
            "status_description": "Part Closure",
            "reason": "Closure near Tower Hill",
        },
    ])

    result = compare_snapshots(previous, current)

    assert len(result) == 1
    assert result.loc[0, "change_type"] == "Unchanged"
