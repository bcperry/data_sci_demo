"""Streamlit dashboard for live earthquake data stored in Delta Lake."""

from datetime import datetime, timezone
from pathlib import Path

from deltalake import DeltaTable
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
DELTA_DIR = ROOT / "notebooks" / "data" / "earthquakes_delta_streamed"
EVENT_COLUMNS = [
    "time_utc",
    "id",
    "date",
    "magnitude",
    "mag_type",
    "type",
    "status",
    "place",
    "tsunami",
    "significance",
    "net",
    "code",
    "ids",
    "sources",
    "types",
    "nst",
    "dmin",
    "rms",
    "gap",
    "alert",
    "url",
    "detail",
    "depth_km",
    "longitude",
    "latitude",
]
SUMMARY_COLUMNS = [
    "time_utc",
    "id",
    "place",
    "magnitude",
    "depth_km",
    "status",
    "url",
    "detail",
]
COLUMN_LABELS = {
    "time_utc": "Time (UTC)",
    "id": "Event ID",
    "date": "Partition Date",
    "magnitude": "Magnitude",
    "mag_type": "Magnitude Type",
    "type": "Event Type",
    "status": "Status",
    "place": "Place",
    "tsunami": "Tsunami",
    "significance": "Significance",
    "net": "Network",
    "code": "Code",
    "ids": "Related IDs",
    "sources": "Sources",
    "types": "Available Products",
    "nst": "Station Count",
    "dmin": "Min Distance",
    "rms": "RMS",
    "gap": "Azimuthal Gap",
    "alert": "Alert Level",
    "url": "USGS Event",
    "detail": "USGS Detail JSON",
    "depth_km": "Depth (km)",
    "longitude": "Longitude",
    "latitude": "Latitude",
}
COLUMN_HELP = {
    "time_utc": "Event timestamp converted from the USGS epoch time.",
    "id": "Stable USGS earthquake identifier.",
    "date": "Date partition persisted in Delta Lake.",
    "magnitude": "Reported earthquake magnitude.",
    "mag_type": "Magnitude scale, such as ml or mb.",
    "type": "USGS event category.",
    "status": "Review status from USGS.",
    "place": "Human-readable location description.",
    "tsunami": "USGS tsunami flag.",
    "significance": "USGS significance score.",
    "net": "Source network code.",
    "code": "Network-specific event code.",
    "ids": "Comma-delimited alternate event identifiers.",
    "sources": "Comma-delimited source network list.",
    "types": "Available product types for the event.",
    "nst": "Number of stations used in the solution.",
    "dmin": "Horizontal distance from station to epicenter.",
    "rms": "Root mean square travel-time residual.",
    "gap": "Largest azimuthal gap between stations.",
    "alert": "USGS alert level when available.",
    "url": "Public USGS event page.",
    "detail": "USGS detail endpoint returning full JSON.",
    "depth_km": "Hypocenter depth in kilometers.",
    "longitude": "Epicenter longitude.",
    "latitude": "Epicenter latitude.",
}
COLUMN_GROUPS = {
    "Core": [
        "time_utc",
        "id",
        "date",
        "place",
        "magnitude",
        "mag_type",
        "type",
        "status",
        "significance",
        "alert",
    ],
    "Location": [
        "latitude",
        "longitude",
        "depth_km",
        "dmin",
        "gap",
        "nst",
        "rms",
        "tsunami",
    ],
    "Metadata": [
        "net",
        "code",
        "ids",
        "sources",
        "types",
        "url",
        "detail",
    ],
}


def ensure_event_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill any missing columns so the UI can always show the full schema."""
    display_df = df.copy()
    for col in EVENT_COLUMNS:
        if col not in display_df.columns:
            display_df[col] = pd.NA
    return display_df.loc[:, EVENT_COLUMNS]


def load_earthquake_data():
    """Load the latest earthquake snapshot and Delta version."""
    dt = DeltaTable(str(DELTA_DIR))
    df = dt.to_pandas()
    return df, dt.version()


def prepare_earthquake_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and sort data for dashboard rendering."""
    plot_df = ensure_event_columns(df)
    plot_df["time_utc"] = pd.to_datetime(plot_df["time_utc"], utc=True, errors="coerce")
    plot_df = plot_df.dropna(subset=["latitude", "longitude", "magnitude"])
    plot_df = plot_df.sort_values("time_utc", ascending=False)
    return plot_df


def build_display_table(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    """Return a full-field table in a stable column order for Streamlit."""
    table_df = ensure_event_columns(df).head(max_rows).copy()
    table_df["time_utc"] = pd.to_datetime(
        table_df["time_utc"], utc=True, errors="coerce"
    )
    return table_df


def build_column_config(columns: list[str]) -> dict:
    """Build column labels, help text, and link rendering for Streamlit tables."""
    config = {}
    for column in columns:
        label = COLUMN_LABELS.get(column, column)
        help_text = COLUMN_HELP.get(column)
        if column in {"url", "detail"}:
            config[column] = st.column_config.LinkColumn(
                label,
                help=help_text,
                display_text="Open link",
            )
        elif column == "time_utc":
            config[column] = st.column_config.DatetimeColumn(
                label,
                help=help_text,
                format="YYYY-MM-DD HH:mm:ss [UTC]",
            )
        elif column in {"magnitude", "depth_km", "dmin", "rms", "gap", "longitude", "latitude"}:
            config[column] = st.column_config.NumberColumn(
                label,
                help=help_text,
                format="%.4f",
            )
        else:
            config[column] = st.column_config.Column(label, help=help_text)
    return config


def render_table(df: pd.DataFrame, columns: list[str], max_rows: int):
    """Render a dataframe slice with shared formatting and metadata."""
    table_df = build_display_table(df, max_rows).loc[:, columns]
    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        column_config=build_column_config(columns),
    )


def render_grouped_tables(df: pd.DataFrame, max_rows: int):
    """Render the wide schema in grouped tabs to keep the UI readable."""
    tabs = st.tabs(list(COLUMN_GROUPS.keys()))
    for tab, (group_name, columns) in zip(tabs, COLUMN_GROUPS.items()):
        with tab:
            st.caption(f"{group_name} fields persisted in Delta Lake")
            render_table(df, columns, max_rows)


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
    fig.update_geos(
        showcountries=True,
        countrycolor="#1f2937",
        countrywidth=0.8,
        showcoastlines=True,
        coastlinecolor="#475569",
        coastlinewidth=0.7,
        showland=True,
        landcolor="#f8fafc",
        showocean=True,
        oceancolor="#dbeafe",
        showlakes=True,
        lakecolor="#dbeafe",
        bgcolor="white",
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

    newest_rows = build_display_table(filtered_df, max_rows)
    changed_rows = build_display_table(
        filtered_df.loc[filtered_df["id"].astype(str).isin(new_ids)], max_rows
    )

    latest_col, changes_col = st.columns(2)
    with latest_col:
        st.subheader("Latest events")
        render_table(newest_rows, SUMMARY_COLUMNS, max_rows)
    with changes_col:
        st.subheader("New on this refresh")
        if changed_rows.empty:
            st.info("No new events since the previous dashboard refresh.")
        else:
            render_table(changed_rows, SUMMARY_COLUMNS, max_rows)

    with st.expander("All persisted fields", expanded=True):
        st.caption("Every normalized field from the USGS feed is available below with labels and grouped sections.")
        render_grouped_tables(filtered_df, max_rows)

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
