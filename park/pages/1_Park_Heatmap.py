"""
First page of Streamlit app: Live crowd heatmap page.
Reads the latest readings (live_status) and refreshes in place every few 
seconds.
"""

import os
import sqlite3
import time

import folium
import pandas as pd
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

DB_PATH     = "park_data.sqlite"
REFRESH_S   = 5   # seconds between in-place updates


def load_current() -> pd.DataFrame:
    try:
        con = sqlite3.connect(DB_PATH)
        df  = pd.read_sql("SELECT * FROM live_status", con)
        con.close()
        return df
    except Exception:
        return pd.DataFrame()


def build_map(df: pd.DataFrame) -> folium.Map:
    def fy(y):                    
        return 100.0 - float(y)     # (100 - y) flips the y so the map reads naturally, with the entrance at the top.

    bounds = [[0, 0], [100, 100]]    # [[lat_min,lng_min],[lat_max,lng_max]]

    m = folium.Map(location=[50, 50], zoom_start=3, crs="Simple", tiles=None,max_bounds=True)
    m.fit_bounds(bounds)
    m.options["minZoom"] = 3            # can't zoom out past the whole image
    m.options["maxZoom"] = 6          
    m.options["maxBounds"] = bounds       # can't pan off the image
    m.options["maxBoundsViscosity"] = 1.0 

    # Image extraction
    if os.path.exists("park_map.png"):
        folium.raster_layers.ImageOverlay(
            image="park_map.png",
            bounds=bounds, opacity=1.0, zindex=1,
        ).add_to(m)

    heat = [[fy(r.y), float(r.x), float(r.occupancy)]
            for r in df.itertuples()]
    HeatMap(heat, radius=35, blur=25, max_zoom=6, min_opacity=0.35).add_to(m)

    for r in df.itertuples():
        color = (
            "#d73027" if r.wait_minutes >= 20 else
            "#fc8d59" if r.wait_minutes >= 10 else
            "#fee090" if r.wait_minutes >= 5  else
            "#91cf60"
        )
        folium.CircleMarker(
            [fy(r.y), float(r.x)], radius=7,
            color="#222", weight=1,
            fill=True, fill_color=color, fill_opacity=0.95,
            tooltip=f"{r.ride_name}  —  {r.wait_minutes:.0f} min wait",
            popup=folium.Popup(
                f"<b>{r.ride_name}</b><br>"
                f"Wait: <b>{r.wait_minutes:.0f} min</b><br>"
                f"Occupancy: {r.occupancy}",
                max_width=160,
            ),
        ).add_to(m)

    return m


def clock_str(minute: int) -> str:
    return f"{9 + minute // 60:02d}:{minute % 60:02d}"


def render():
    st.set_page_config(page_title="Park Heatmap", layout="wide")
    st.markdown("<h1><b><u>Park Heatmap</u></b></h1>", unsafe_allow_html=True)
    st.caption(
        "Dot colours: 🔴 20+ min  🟠 10-19 min  🟡 5-9 min  🟢 <5 min. "
        "Click any dot for details."
    )

    # Placeholders so that Streamlit only replaces specific panels in place
    header_ph = st.empty()
    cols      = st.columns([3, 1])
    map_ph    = cols[0].empty()
    waits_ph  = cols[1].empty()
    status_ph = st.empty()

    while True:
        df = load_current()

        if df.empty:
            header_ph.warning(
                "No live data yet — start the simulator:\n\n"
                "```\npython run_local.py --speed 3\n```"
            )
            time.sleep(2)
            continue

        minute       = int(df.park_minute.iloc[0])
        total_guests = int(df.occupancy.sum())
        top_wait     = df.loc[df.wait_minutes.idxmax()]

        # --- HEADER METRICS ---
        with header_ph.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Simulated time",        clock_str(minute))
            c2.metric("Guests in rides/queues", total_guests)
            c3.metric("Longest wait",
                      f"{top_wait.wait_minutes:.0f} min",
                      top_wait.ride_name)
            c4.metric("Simulated minute",      f"{minute} / 720")

        # --- MAP ---
        with map_ph.container():
            st_folium(build_map(df), width=750, height=520,
                      returned_objects=[])

        # --- WAIT TIME SIDEBAR ---
        with waits_ph.container():
            st.subheader("Longest waits")
            for r in df.sort_values("wait_minutes", ascending=False).head(5).itertuples():
                st.metric(r.ride_name, f"{r.wait_minutes:.0f} min",
                          f"{r.occupancy} guests", delta_color="off")
            st.divider()
            st.subheader("Walk right on")
            for r in df.sort_values("wait_minutes").head(3).itertuples():
                st.metric(r.ride_name, f"{r.wait_minutes:.0f} min wait")

        status_ph.caption(f"Last updated: {clock_str(minute)}  —  "
                          f"refreshing every {REFRESH_S}s")
        time.sleep(REFRESH_S)


if __name__ == "__main__":
    render()