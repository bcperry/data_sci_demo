# Data Science Demo: Earthquake Streaming to Delta Lake

A real-time data ingestion pipeline that streams earthquake data from the USGS GeoJSON API into Delta Lake tables, with automatic date-based partitioning.

## Overview

This project demonstrates:
- **Real-time data streaming**: Continuously fetches earthquake data from the USGS Earthquake Hazards Program API
- **Delta Lake integration**: Stores data in Delta Lake format with automatic versioning and schema management
- **Partitioned storage**: Organizes data by date for efficient querying
- **Schema normalization**: Handles data type coercion and validation
- **Idempotent ingestion**: Tracks unique events to avoid duplicates during streaming

## Features

- **Live earthquake data**: Polls the USGS "all_hour" feed for recent seismic activity
- **Automatic Delta Lake versioning**: Tracks all schema changes and data mutations
- **GeoJSON parsing**: Extracts coordinates, magnitude, location, and event metadata
- **Type-safe schema**: Ensures consistent numeric, string, and datetime types
- **Partition pruning**: Date-partitioned storage for efficient analytics queries

## Project Structure

```
.
├── main.py                          # Main streaming application
├── notebooks/
│   ├── streaming_delta_ingestion.ipynb  # Analysis notebook
│   └── data/
│       └── earthquakes_delta_streamed/  # Delta Lake table directory
│           ├── _delta_log/              # Delta transaction log
│           └── date=YYYY-MM-DD/         # Date partitions
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project configuration
└── README.md                        # This file
```

## Installation

### Prerequisites
- Python 3.12+
- `uv` package manager (recommended) or `pip`

### Setup

```bash
# Clone and navigate to project
cd data_sci_demo

# Install dependencies with uv
uv sync

# Or with pip
pip install -r requirements.txt
```

## Usage

### Run the streaming application

```bash
# Stream earthquake data with the default 5-second poll interval
uv run main.py

# Stream earthquake data with a custom 10-second poll interval
uv run main.py 10

# Or with pip
python main.py

# Or with a custom interval
python main.py 10
```

If omitted, the poll interval defaults to 5 seconds. The application will:
1. Fetch latest earthquakes from USGS API
2. Identify new events (by ID) not already in the Delta table
3. Write new events to Delta Lake with automatic date partitioning
4. Continue polling until interrupted (Ctrl+C)

### Run the live dashboard

Start the ingestion job in one terminal:

```bash
uv run main.py
```

Then start the Streamlit dashboard in a second terminal:

```bash
uv run streamlit run viewer.py
```

The dashboard refreshes automatically and shows:
- the latest Delta table version
- new earthquake events detected since the previous refresh
- a live map filtered by magnitude
- the most recent rows from the Delta table

If you are using WSL and the browser does not open automatically, open `http://localhost:8501` from Windows or run:

```bash
explorer.exe http://localhost:8501
```

### Example output

```
Loaded 150 existing earthquake IDs from Delta table
Current Delta table version: 3
[Poll 1] Fetched 45 events, 12 new
  ✓ Appended 12 rows to Delta table
  Total unique events tracked: 162

[Poll 2] Fetched 43 events, 8 new
  ✓ Appended 8 rows to Delta table
  Total unique events tracked: 170

...
```

### Analysis notebook

Open `notebooks/streaming_delta_ingestion.ipynb` for analysis and visualization of the earthquake data.

## Dependencies

- **deltalake** (≥1.2.1): Delta Lake Python API
- **pandas** (≥2.3.3): Data manipulation
- **pyarrow** (≥22.0.0): Apache Arrow support for Delta Lake
- **geopandas** (≥1.1.1): Geospatial data analysis
- **requests** (≥2.32.5): HTTP requests to USGS API
- **plotly** (≥6.5.0): Interactive visualizations
- **streamlit** (≥1.55.0): Live dashboard UI

## Data Schema

Each earthquake record contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | USGS event ID |
| `date` | string | Event date (partition field) |
| `time_utc` | timestamp | Event time in UTC |
| `magnitude` | float | Earthquake magnitude |
| `mag_type` | string | Magnitude scale type |
| `place` | string | Location description |
| `depth_km` | float | Depth in kilometers |
| `longitude` | float | Geographic longitude |
| `latitude` | float | Geographic latitude |
| `tsunami` | int | Tsunami warning indicator |
| `significance` | int | USGS computed significance |
| Other fields | various | Additional USGS metadata |

## Data Source

**USGS Earthquake Hazards Program** - Latest earthquake feed
- Endpoint: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson`
- Updates: Approximately every minute
- Coverage: Global seismic events in the past hour

## Architecture

### Streaming Ingestion Process

1. **API Polling**: Periodically fetches earthquake events from USGS GeoJSON endpoint
2. **Normalization**: Extracts and transforms GeoJSON features into tabular format
3. **Deduplication**: Tracks unique event IDs to prevent duplicate ingestion
4. **Schema Coercion**: Ensures all columns match expected types (strings, timestamps, floats, etc.)
5. **Delta Write**: Appends new records to Delta Lake with date-based partitioning
6. **Versioning**: Automatic transaction logging maintains data lineage and enables time travel

## Development

### Running with development dependencies

```bash
uv sync --group dev
```

This installs:
- `ipykernel`: Jupyter notebook kernel support
- `pre-commit`: Git hooks for code quality

## Notes

- The Delta table persists in `notebooks/data/earthquakes_delta_streamed/`
- Only new earthquake events (by ID) are written to Delta Lake
- Date partitioning enables efficient filtering: `date=2025-12-12/`, `date=2025-12-11/`, etc.
- The Delta transaction log (`_delta_log/`) tracks all schema and data changes for reproducibility
- Interrupting the stream (Ctrl+C) is safe—the next run will resume from existing data

## License

MIT
