# TfL Event Travel Monitor

## 1. What I built and who for

I built a Python data pipeline and interactive dashboard that monitors reported London Underground service statuses using the TfL Unified API.

The project is designed for an **event operations coordinator planning staff or contractor travel to an event in London**. Service disruptions can affect journey plans, so I wanted to explore how public transport data could be turned into useful operational information.

The dashboard allows users to:
- View the latest reported status and available disruption details for each Underground line.
- Identify changes in reported service status between observations.
- Explore historical observations for a selected line.
- View reported status severity over time.
- Trigger a fresh data collection directly from the dashboard.

The aim was to build a complete, repeatable data workflow rather than just retrieve API data or create a standalone visualisation.

This is an independent portfolio project, not an official TfL product or a journey-planning service.

## 2. The data

**Source:** [TfL Unified API](https://api.tfl.gov.uk/)

**API documentation:** [TfL API documentation](https://api.tfl.gov.uk/Help)

**Endpoint used:** `GET /Line/Mode/tube/Status`

### API access

This project currently retrieves data without an API key, so no account setup is required for the existing implementation. TfL recommends registering for an API account, which provides access to API keys and higher request limits. If anonymous access changes or the project requires higher request volumes, the API client may need to be updated to use a key.

For details, see the [TfL API portal](https://api-portal.tfl.gov.uk/) and its [access and subscription information](https://api-portal.tfl.gov.uk/products).

The endpoint returns the currently reported status information for London Underground lines. I used it to retrieve the line identifiers and names, status severity, status descriptions and any available disruption explanations.

The API response is nested JSON. Some lines have no disruption reason when reporting Good Service, while others include additional text describing the disruption. The pipeline accounts for these differences when transforming the data.

The API provides current status information rather than a historical archive. To build a history, the project saves timestamped snapshots of the responses it collects. This means historical coverage grows as the pipeline is run over time.

The snapshots include the time of collection in UTC, allowing observations to be compared chronologically. A change between two snapshots indicates that the reported information differed between those observations; it does not establish exactly when an underlying incident began or ended.

Before wider or automated use, the applicable TfL API terms, attribution requirements and data-reuse conditions should be checked.

## 3. How it works

The project follows an extract, transform, validate and load workflow, with a comparison stage and a Streamlit dashboard.

1. **Extract:** Python's `requests` library calls the TfL endpoint and retrieves the JSON response.
2. **Preserve raw data:** each response is saved locally as a timestamped JSON snapshot so it can be inspected or reprocessed.
3. **Transform:** pandas converts the nested response into structured records containing collection time, line ID, line name, status severity, status description and disruption reason.
4. **Validate:** the pipeline checks required columns, missing key values and whether severity values are numeric. If validation fails, the data is not loaded.
5. **Compare:** the latest snapshot is compared with an earlier snapshot to identify reported status changes, transitions into or out of Good Service, and changes to disruption explanations.
6. **Load:** observations are stored in a local DuckDB database. A processed-snapshot registry prevents the same snapshot file from being loaded twice.
7. **Present:** Streamlit displays the latest observations, reported changes, historical records and a status-severity chart. A dashboard button triggers the pipeline and refreshes the displayed data.

### Key decisions

- **DuckDB for storage:** I chose DuckDB to store structured observations and support historical analysis in a lightweight local database.
- **Keep raw snapshots:** preserving the original JSON separates data collection from transformation and makes it possible to inspect or reprocess source data.
- **Validate before loading:** basic data-quality checks help prevent incomplete or incorrectly structured data from entering the database.
- **Compare observations rather than invent incident timelines:** the API provides current status, so the project only claims to identify differences between the snapshots it has collected.
- **Build a simple user-facing dashboard:** Streamlit provides a practical way to make the pipeline's output accessible without building a separate frontend.

The main components are `src/collect.py`, `src/transform.py`, `src/validate.py`, `src/compare.py`, `src/database.py` and `src/pipeline.py`, with `app.py` providing the dashboard.

## 4. How to run it

### Requirements

- Python 3.
- An internet connection to retrieve data from TfL.
- The dependencies listed in `requirements.txt`.

### Setup

Clone the repository:

```bash
git clone https://github.com/kvirdee365-ui/information-lab-application-kvirdee365.git
cd information-lab-application-kvirdee365
```

Create and activate a virtual environment.

On Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run the pipeline

```bash
python -m src.pipeline
```

This retrieves a new snapshot, transforms and validates the data, compares it with an earlier snapshot if one is available, and loads the observations into DuckDB.

The raw snapshots and database are generated locally, so a new user should not need an existing database to get started.

### Launch the dashboard

```bash
streamlit run app.py
```

Open the local URL printed in the terminal. Use the **Refresh TfL data** button to collect and process another observation from within the dashboard.

### Run the tests

```bash
python -m pytest
```

The automated tests currently cover the snapshot comparison logic, including unchanged statuses, status changes, changes in disruption reasons, and lines appearing or disappearing between snapshots.

## 5. What I would do next

There are several improvements I would make to develop the project further.

- **Expand automated testing:** add tests for data validation, database loading, duplicate prevention and pipeline failure scenarios.
- **Improve historical analysis:** collect observations over a longer period and make it easier to identify recurring disruption patterns. The current dataset is limited by how often snapshots have been collected.
- **Improve the dashboard:** refine how disrupted lines are highlighted and make the historical chart more informative as additional observations accumulate.
- **Automate collection:** investigate a scheduled collection process so that historical data can grow without relying on manual refreshes.
- **Improve deployment and reproducibility:** test the complete setup from a clean checkout and explore hosting the dashboard and database workflow.
- **Verify data-reuse requirements:** confirm the relevant API terms and attribution requirements before expanding the project's collection or distribution.

My immediate priority would be to strengthen automated testing and verify that the entire project can be reproduced from a clean checkout. That would give me more confidence in the pipeline's reliability before adding further functionality.

## 6. Where AI helped

I used AI as a development assistant while building the project, particularly because I am still developing my Python and data engineering skills.

It helped me break the project into manageable stages, understand API responses, structure the pipeline, work through Python errors, and explore concepts such as data validation, database loading, snapshot comparison and Streamlit dashboards.

I reviewed and tested the code as I developed it, rather than treating generated code as automatically correct. For example, I tested the database loader by running it twice and verifying that the same snapshot was not loaded twice. I also ran the automated comparison tests and exercised the dashboard's refresh workflow.

I made decisions about the project's intended user, the data source, the pipeline stages and the features to include. I also adjusted the implementation as issues emerged during testing.


