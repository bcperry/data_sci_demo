import argparse
from deltalake import write_deltalake, DeltaTable
import pandas as pd
from pathlib import Path
import requests
import time
from datetime import datetime, timezone
from pandas import StringDtype


ROOT = Path(__file__).parent
DELTA_DIR = ROOT / "notebooks" / "data" / "earthquakes_delta_streamed"

# Create the delta directory
DELTA_DIR.mkdir(parents=True, exist_ok=True)

# USGS GeoJSON API endpoint — use "all_day" by default for broader global
# coverage (the "all_hour" feed rarely contains events from less seismically
# active regions such as Europe and the Middle East).
VALID_FEEDS = ("all_hour", "all_day", "all_week", "all_month")
DEFAULT_FEED = "all_day"
USGS_FEED_BASE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"
USGS_GEOJSON_URL = f"{USGS_FEED_BASE}/{DEFAULT_FEED}.geojson"


def normalize_feature(feature):
    """Extract normalized earthquake data from USGS GeoJSON feature"""
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [None, None, None])
    ts = props.get("time")
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if ts else None
    return {
        "id": feature.get("id"),
        "date": dt.date() if dt else None,
        "time_utc": dt,
        "magnitude": props.get("mag"),
        "mag_type": props.get("magType"),
        "type": props.get("type"),
        "status": props.get("status"),
        "place": props.get("place"),
        "tsunami": props.get("tsunami"),
        "significance": props.get("sig"),
        "net": props.get("net"),
        "code": props.get("code"),
        "ids": props.get("ids"),
        "sources": props.get("sources"),
        "types": props.get("types"),
        "nst": props.get("nst"),
        "dmin": props.get("dmin"),
        "rms": props.get("rms"),
        "gap": props.get("gap"),
        "alert": props.get("alert"),
        "url": props.get("url"),
        "detail": props.get("detail"),
        "depth_km": coords[2] if len(coords) > 2 else None,
        "longitude": coords[0],
        "latitude": coords[1],
    }


def fetch_events(url=USGS_GEOJSON_URL, timeout=10):
    """Fetch current earthquake events from USGS feed"""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return [normalize_feature(f) for f in data.get("features", [])]
    except Exception as e:
        print(f"[warn] fetch error: {e}")
        return []


def coerce_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure consistent schema for Delta Lake"""
    # Ensure datetime with UTC
    if "time_utc" in df.columns:
        df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, errors="coerce")
    # Ensure date is ISO string (partition field)
    if "date" in df.columns:
        df["date"] = df["date"].astype("string")
    # String fields
    for col in [
        "id",
        "place",
        "mag_type",
        "type",
        "status",
        "net",
        "code",
        "ids",
        "sources",
        "types",
        "alert",
        "url",
        "detail",
    ]:
        if col in df.columns:
            df[col] = df[col].astype(StringDtype())
    # Numeric floats
    for col in [
        "magnitude",
        "depth_km",
        "longitude",
        "latitude",
        "dmin",
        "rms",
        "gap",
        "significance",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Integers (nullable)
    for col in ["nst", "tsunami"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def main(poll_interval: int = 5, feed: str = DEFAULT_FEED):
    feed_url = f"{USGS_FEED_BASE}/{feed}.geojson"
    print(f"Using USGS feed: {feed_url}")
    delta_path = str(DELTA_DIR)
    events = {}  # Track unique events by ID

    # Load existing earthquake IDs from Delta table if it exists
    try:
        existing_dt = DeltaTable(delta_path)
        existing_df = existing_dt.to_pandas()
        existing_ids = set(existing_df["id"].dropna().tolist())
        # Populate events dictionary with existing data
        for _, row in existing_df.iterrows():
            events[row["id"]] = row.to_dict()
        print(f"Loaded {len(existing_ids)} existing earthquake IDs from Delta table")
        print(f"Current Delta table version: {existing_dt.version()}")
    except Exception:
        existing_ids = set()
        print("Starting fresh - no existing Delta table found")

    iteration = 0

    try:
        while True:
            iteration += 1

            # Fetch new events from API
            new_feats = fetch_events(url=feed_url)
            new_count = 0

            for ev in new_feats:
                eid = ev.get("id")
                if eid and eid not in events:
                    events[eid] = ev
                    new_count += 1

            print(
                f"[Poll {iteration}] Fetched {len(new_feats)} events, {new_count} new"
            )

            # Write new events to Delta Lake
            if new_count > 0:
                # Get the new events
                new_event_list = [
                    events[eid] for eid in list(events.keys())[-new_count:]
                ]
                df_new = pd.DataFrame(new_event_list)

                # Coerce dtypes to avoid Null-type schema errors
                df_new = coerce_schema(df_new)

                # Write to Delta Lake
                if len(existing_ids) == 0 and iteration == 1:
                    # First write ever: create table
                    write_deltalake(
                        delta_path, df_new, mode="overwrite", partition_by=["date"]
                    )
                    print(f"  ✓ Created Delta table with {len(df_new)} rows")
                else:
                    # Append new data
                    write_deltalake(
                        delta_path, df_new, mode="append", partition_by=["date"]
                    )
                    print(f"  ✓ Appended {len(df_new)} rows to Delta table")

            print(f"  Total unique events tracked: {len(events)}\n")

            # Wait before next poll
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print(f"\nStream interrupted by user after {iteration} polls.")

    print(f"\n✓ Streaming complete! Total unique events: {len(events)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stream earthquake data from USGS to Delta Lake"
    )
    parser.add_argument(
        "refresh_rate",
        nargs="?",
        default=5,
        type=int,
        help="Poll interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--feed",
        choices=VALID_FEEDS,
        default=DEFAULT_FEED,
        help=(
            f"USGS feed time window (default: {DEFAULT_FEED}). "
            "Wider windows (all_week, all_month) include more events from "
            "less seismically active regions."
        ),
    )
    args = parser.parse_args()
    main(args.refresh_rate, feed=args.feed)
