
import json
from datetime import datetime, timezone
from pathlib import Path

from src.tfl_client import fetch_tube_status


def collect_tube_status():
    """Fetch Tube status and save a timestamped raw JSON snapshot."""

    # Fetch the latest data from TfL.
    lines = fetch_tube_status()

    # Record when our pipeline collected the response.
    collected_at = datetime.now(timezone.utc)

    # Create a unique filename for this collection.
    timestamp = collected_at.strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"tube_status_{timestamp}.json"

    # Preserve the API response alongside our collection timestamp.
    snapshot = {
        "collected_at": collected_at.isoformat(),
        "source": "TfL Unified API",
        "endpoint": "Line/Mode/tube/Status",
        "line_count": len(lines),
        "data": lines,
    }

    # Save the snapshot as readable JSON.
    output_file.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Collected {len(lines)} Tube lines.")
    print(f"Collection time (UTC): {collected_at.isoformat()}")
    print(f"Saved raw snapshot to: {output_file}")

    return output_file

if __name__ == "__main__":
    collect_tube_status()
