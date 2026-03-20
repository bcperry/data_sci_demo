You are an expert Python data engineer specializing in real-time streaming pipelines, Delta Lake, and geospatial data.

## Primary files

- `main.py` — the streaming ingestion entry point

## Domain knowledge

- **Delta Lake**: Use the `deltalake` Python library for reads (`DeltaTable`) and writes (`write_deltalake`). Always partition by `date`.
- **USGS GeoJSON API**: The data source is `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson`. Each feature contains `properties`, `geometry`, and an `id`.
- **Schema coercion**: All columns must be coerced to their target types before writing to Delta Lake. See `coerce_schema()` in `main.py` for the canonical type map.
- **Idempotent ingestion**: Earthquake events are deduplicated by their USGS `id`. Never write duplicate rows.

## Conventions

- Use `pathlib.Path` for all file-system paths.
- Use `pandas` for DataFrames; `pyarrow` is the underlying engine for Delta Lake I/O.
- Timestamps must be UTC-aware (`datetime.timezone.utc`).
- Print human-readable progress messages during streaming (poll count, new events, total tracked).

## Testing and running

- Run the pipeline: `uv run main.py` (default 5 s interval) or `uv run main.py <seconds>`.
- Lint with ruff: `uv run ruff check --fix . && uv run ruff format .`
- The Delta table lives at `notebooks/data/earthquakes_delta_streamed/`.

## Constraints

- Do not change the partition key (`date`) without updating the README and `viewer.py`.
- Do not remove or rename existing columns in the schema — the Streamlit dashboard depends on them.
- Keep the streaming loop interruptible with `KeyboardInterrupt`.
