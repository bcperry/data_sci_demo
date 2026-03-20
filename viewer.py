"""Streamlit dashboard for live earthquake data stored in Delta Lake."""

from datetime import datetime, timezone
from pathlib import Path

from deltalake import DeltaTable
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
DELTA_DIR = ROOT / "notebooks" / "data" / "earthquakes_delta_streamed"


def load_earthquake_data():
    """Load the latest earthquake snapshot and Delta version."""
    dt = DeltaTable(str(DELTA_DIR))
    df = dt.to_pandas()
    return df, dt.version()


def prepare_earthquake_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and sort data for dashboard rendering."""
    plot_df = df.copy()
    plot_df["time_utc"] = pd.to_datetime(plot_df["time_utc"], utc=True, errors="coerce")
    plot_df = plot_df.dropna(subset=["latitude", "longitude", "magnitude"])
    plot_df = plot_df.sort_values("time_utc", ascending=False)
    return plot_df


def create_map_view(df: pd.DataFrame):
    """Build the geographic scatter plot for current events."""
    fig = px.scatter_geo(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="place",
        hover_data={
            "magnitude": ":.2f",
            "depth_km": ":.2f",
            "time_utc": True,
            "latitude": ":.4f",
            "longitude": ":.4f",
        },
        size="magnitude",
        color="magnitude",
        color_continuous_scale="Reds",
        size_max=18,
        projection="natural earth",
        title="Live Earthquake Locations",
    )
    fig.update_layout(height=650, margin={"l": 0, "r": 0, "t": 60, "b": 0})
    return fig


def initialize_session_state():
    """Initialize persisted dashboard state across refreshes."""
    st.session_state.setdefault("seen_ids", [])
    st.session_state.setdefault("last_version", None)
    st.session_state.setdefault("last_refresh_utc", None)


def render_metrics(total_rows: int, visible_rows: int, new_rows: int, version: int):
    """Render summary metrics for the current snapshot."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total rows", total_rows)
    col2.metric("Visible on map", visible_rows)
    col3.metric("New since last refresh", new_rows)
    version_delta = None
    if st.session_state["last_version"] is not None:
        version_delta = version - st.session_state["last_version"]
    col4.metric("Delta version", version, delta=version_delta)


def render_dashboard(refresh_interval: int, min_magnitude: float, max_rows: int):
    """Render the current dashboard snapshot."""
    try:
        raw_df, version = load_earthquake_data()
    except Exception as exc:
        st.error(f"Unable to load Delta table from {DELTA_DIR}: {exc}")
        st.info("Start the ingestion process first with `uv run main.py`.")
        return

    if raw_df.empty:
        st.warning("The Delta table is present but contains no rows yet.")
        return

    plot_df = prepare_earthquake_data(raw_df)
    filtered_df = plot_df.loc[plot_df["magnitude"] >= min_magnitude].copy()

    current_ids = set(filtered_df["id"].dropna().astype(str))
    previous_ids = set(st.session_state["seen_ids"])
    new_ids = current_ids - previous_ids

    render_metrics(
        total_rows=len(raw_df),
        visible_rows=len(filtered_df),
        new_rows=len(new_ids),
        version=version,
    )

    last_refresh = datetime.now(timezone.utc)
    st.caption(
        f"Auto-refresh every {refresh_interval}s. Last refresh: {last_refresh.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    if filtered_df.empty:
        st.warning("No rows match the current filters.")
    else:
        st.plotly_chart(create_map_view(filtered_df), width="stretch")

    newest_rows = filtered_df.head(max_rows)
    changed_rows = filtered_df.loc[filtered_df["id"].astype(str).isin(new_ids)].head(
        max_rows
    )

    latest_col, changes_col = st.columns(2)
    with latest_col:
        st.subheader("Latest events")
        st.dataframe(
            newest_rows[["time_utc", "id", "place", "magnitude", "depth_km", "status"]],
            width="stretch",
            hide_index=True,
        )
    with changes_col:
        st.subheader("New on this refresh")
        if changed_rows.empty:
            st.info("No new events since the previous dashboard refresh.")
        else:
            st.dataframe(
                changed_rows[
                    ["time_utc", "id", "place", "magnitude", "depth_km", "status"]
                ],
                width="stretch",
                hide_index=True,
            )

    with st.expander("Raw data snapshot"):
        st.dataframe(filtered_df.head(max_rows), width="stretch", hide_index=True)

    st.session_state["seen_ids"] = list(current_ids)
    st.session_state["last_version"] = version
    st.session_state["last_refresh_utc"] = last_refresh.isoformat()


def main():
    """Configure and run the Streamlit dashboard."""
    st.set_page_config(page_title="Earthquake Stream", page_icon="🌍", layout="wide")
    initialize_session_state()

    st.title("Earthquake Stream Dashboard")
    st.write(
        "Watch the Delta table update in real time while the ingestion process appends new USGS events."
    )

    with st.sidebar:
        st.header("Controls")
        auto_refresh = st.toggle("Auto refresh", value=True)
        refresh_interval = st.slider(
            "Refresh interval (seconds)", min_value=1, max_value=30, value=5
        )
        min_magnitude = st.slider(
            "Minimum magnitude",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.1,
        )
        max_rows = st.slider(
            "Rows to show", min_value=10, max_value=100, value=25, step=5
        )
        st.button("Refresh now", width="stretch")

    run_every = f"{refresh_interval}s" if auto_refresh else None

    @st.fragment(run_every=run_every)
    def live_dashboard():
        render_dashboard(refresh_interval, min_magnitude, max_rows)

    live_dashboard()


main()
