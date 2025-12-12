"""
Interactive Plotly viewer for earthquake data from Delta Lake
"""

from pathlib import Path
import plotly.express as px
from deltalake import DeltaTable

ROOT = Path(__file__).parent
DELTA_DIR = ROOT / "notebooks" / "data" / "earthquakes_delta_streamed"


def load_earthquake_data():
    """Load earthquake data from Delta Lake"""
    dt = DeltaTable(str(DELTA_DIR))
    df = dt.to_pandas()
    return df


def create_map_view(df):
    """Create an interactive map of earthquake locations"""
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
        title="Earthquake Locations",
        size_max=20,
        projection="natural earth",
    )
    fig.update_layout(height=700, width=1000)
    return fig


def main():
    """Load data and display interactive earthquake map"""
    print("Loading earthquake data from Delta Lake...")
    df = load_earthquake_data()

    print(f"Loaded {len(df)} earthquakes")
    print(f"Magnitude range: {df['magnitude'].min():.2f} - {df['magnitude'].max():.2f}")
    print(f"Depth range: {df['depth_km'].min():.2f} - {df['depth_km'].max():.2f} km")
    print()

    # Create and display the earthquake map
    print("Displaying interactive earthquake map...\n")
    fig_map = create_map_view(df)
    fig_map.show()


if __name__ == "__main__":
    main()
