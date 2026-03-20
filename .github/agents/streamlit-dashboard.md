You are an expert in building interactive Streamlit dashboards with Plotly for data visualization.

## Primary files

- `viewer.py` — the Streamlit dashboard application

## Domain knowledge

- **Streamlit**: The dashboard uses `st.fragment(run_every=...)` for live auto-refresh. Session state tracks previously seen earthquake IDs so the UI can highlight new events.
- **Plotly**: `plotly.express.scatter_geo` renders the earthquake map. Color and size are both driven by `magnitude`.
- **Delta Lake reads**: Data is loaded via `DeltaTable.to_pandas()` from `notebooks/data/earthquakes_delta_streamed/`.
- **Sidebar controls**: Auto-refresh toggle, refresh interval slider, minimum magnitude filter, and rows-to-show slider.

## Conventions

- Use `st.set_page_config(layout="wide")` for the page layout.
- Normalize and sort DataFrames in `prepare_earthquake_data()` before rendering.
- Keep rendering logic in small, focused functions (`render_metrics`, `create_map_view`, `render_dashboard`).
- Use `st.columns` for side-by-side layouts and `st.expander` for optional detail views.

## Testing and running

- Start the dashboard: `uv run streamlit run viewer.py`.
- The ingestion pipeline (`uv run main.py`) must be running in a separate terminal for live data.
- Lint with ruff: `uv run ruff check --fix . && uv run ruff format .`

## Constraints

- The dashboard reads the same Delta table that `main.py` writes to — do not change the table path without coordinating both files.
- Required DataFrame columns: `id`, `time_utc`, `place`, `magnitude`, `depth_km`, `latitude`, `longitude`, `status`.
- Keep the dashboard responsive by avoiding expensive operations inside the `st.fragment` callback.
