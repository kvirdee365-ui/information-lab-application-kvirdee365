from src.pipeline import run_pipeline
import pandas as pd
import streamlit as st

from src.compare import compare_snapshots
from src.database import load_observations


st.set_page_config(
    page_title="TfL Event Travel Monitor",
    page_icon="🚇",
    layout="wide",
)

st.title("TfL Event Travel Monitor")
st.write(
    "Monitor reported London Underground statuses and identify "
    "changes that could affect travel to an event."
)

if "refresh_message" not in st.session_state:
    st.session_state["refresh_message"] = None

if st.button("Refresh TfL data", type="primary"):
    try:
        with st.spinner("Collecting and processing the latest TfL data..."):
            success = run_pipeline()

        if success:
            st.session_state["refresh_message"] = (
                "TfL data refreshed successfully."
            )
            st.rerun()
        else:
            st.error(
                "The pipeline could not complete because validation failed. "
                "Check the terminal output for details."
            )

    except Exception as error:
        st.error(f"Refresh failed: {error}")

if st.session_state["refresh_message"]:
    st.success(st.session_state["refresh_message"])
    st.session_state["refresh_message"] = None


try:
    history = load_observations()
except FileNotFoundError:
    st.error(
        "No database found. Run `python -m src.pipeline` first."
    )
    st.stop()

if history.empty:
    st.warning(
        "No observations found. Run `python -m src.pipeline` first."
    )
    st.stop()

history["collected_at"] = pd.to_datetime(
    history["collected_at"], utc=True
)

latest_time = history["collected_at"].max()
current = history[history["collected_at"] == latest_time].copy()

st.caption(
    f"Latest observation collected at "
    f"{latest_time.strftime('%d %b %Y, %H:%M:%S UTC')}"
)

not_good_service = current[
    current["status_description"].str.casefold()
    .ne("good service")
    .fillna(True)
]

col1, col2, col3 = st.columns(3)

col1.metric("Tube lines observed", current["line_id"].nunique())
col2.metric("Not reporting Good Service", len(not_good_service))
col3.metric("Historical observations", len(history))

st.subheader("Current reported status")

display_columns = [
    "line_name",
    "status_description",
    "reason",
]

st.dataframe(
    current[display_columns].sort_values("line_name"),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Changes since the previous observation")

observation_times = sorted(history["collected_at"].unique())

if len(observation_times) >= 2:
    previous_time = observation_times[-2]

    previous = history[
        history["collected_at"] == previous_time
    ].copy()

    changes = compare_snapshots(previous, current)

    changed = changes[
        changes["change_type"] != "Unchanged"
    ]

    if changed.empty:
        st.success("No reported status changes detected.")
    else:
        st.dataframe(
            changed,
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info(
        "Collect another snapshot to enable comparison "
        "with a previous observation."
    )

st.subheader("Observation history")

line_names = sorted(history["line_name"].dropna().unique())

selected_line = st.selectbox(
    "Choose a Tube line",
    line_names,
)

line_history = history[
    history["line_name"] == selected_line
].sort_values("collected_at")

st.markdown(f"#### {selected_line} status over time")

if line_history.empty:
    st.info("No historical observations are available for this line.")
else:
    chart_data = line_history[
        ["collected_at", "status_severity", "status_description"]
    ].copy()

    chart_data = chart_data.dropna(subset=["status_severity"])

    if chart_data.empty:
        st.info("No numeric status severity data is available to chart.")
    else:
        chart_data = chart_data.sort_values("collected_at")

        st.line_chart(
            chart_data,
            x="collected_at",
            y="status_severity",
            x_label="Observation time (UTC)",
            y_label="TfL status severity",
        )

        st.caption(
            "TfL severity values are plotted over time. "
            "Lower values generally indicate better service; "
            "the chart shows collected observations, not continuous monitoring."
        )

st.dataframe(
    line_history[
        [
            "collected_at",
            "status_description",
            "reason",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Data source: TfL Unified API. Statuses are observations at "
    "collection times, not a complete record of every incident."
)
