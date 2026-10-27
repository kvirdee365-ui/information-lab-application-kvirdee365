import json
import requests

TFL_STATUS_URL = "https://api.tfl.gov.uk/Line/Mode/tube/Status"


def fetch_tube_status():
    """Fetch the current reported status of London Underground lines."""
    response = requests.get(TFL_STATUS_URL, timeout=30)

    # Raise an error if TfL returns an unsuccessful HTTP status.
    response.raise_for_status()

    # Convert the JSON response into Python data.
    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected API response: expected a list.")

    return data


if __name__ == "__main__":
    lines = fetch_tube_status()

    print(f"Successfully retrieved {len(lines)} Tube lines.\n")

    for line in lines:
        print(f"Line: {line.get('name', 'Unknown')}")

        statuses = line.get("lineStatuses", [])
        for status in statuses:
            print(
                f"  Status: "
                f"{status.get('statusSeverityDescription', 'Unknown')}"
            )

            reason = status.get("reason")
            if reason:
                print(f"  Details: {reason}")

        print()
    # Print the complete JSON record for the first line.
    print("FULL JSON RECORD FOR FIRST LINE:")
    print(json.dumps(lines[0], indent=2))