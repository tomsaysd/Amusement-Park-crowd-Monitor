"""
First page of Streamlit app: Live crowd heatmap page.
Reads the latest readings (live_status) and refreshes in place every few seconds.
"""

import time
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from bigquery_reader import load_history

REFRESH_S = 5


def load_current() -> pd.DataFrame:
    try:
        df = load_history()

        if df.empty:
            return df

        latest_minute = df["park_min"].max()
        return df[df["park_min"] == latest_minute]

    except Exception as e:
        print(e)
        return pd.DataFrame()


def build_map(df: pd.DataFrame) -> folium.Map:

    def fy(y):
        return 100.0 - float(y)

    bounds = [[10, 15], [90, 90]]

    m = folium.Map(
        location=[50, 50],
        zoom_start=5,
        crs="Simple",
        tiles=None,
        max_bounds=True,
    )

    m.fit_bounds(bounds)

    m.options["minZoom"] = 3
    m.options["maxZoom"] = 6
    m.options["maxBounds"] = bounds
    m.options["maxBoundsViscosity"] = 1.0

    MAP_PATH = Path(__file__).parent.parent / "park_map.png"

    if MAP_PATH.exists():
        folium.raster_layers.ImageOverlay(
            image=str(MAP_PATH),
            bounds=bounds,
            opacity=1,
        ).add_to(m)

    heat = [
        [fy(r.y), float(r.x), float(r.occupency)]
        for r in df.itertuples()
    ]

    HeatMap(
        heat,
        radius=35,
        blur=25,
        max_zoom=6,
        min_opacity=0.35,
    ).add_to(m)

    for r in df.itertuples():

        color = (
            "#d73027" if r.wait_mins >= 20
            else "#fc8d59" if r.wait_mins >= 10
            else "#fee090" if r.wait_mins >= 5
            else "#91cf60"
        )

        folium.CircleMarker(
            [fy(r.y), float(r.x)],
            radius=7,
            color="#222",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=f"{r.ride_name} — {r.wait_mins:.0f} min wait",
            popup=folium.Popup(
                f"<b>{r.ride_name}</b><br>"
                f"Wait: <b>{r.wait_mins:.0f} min</b><br>"
                f"Occupancy: {r.occupency}",
                max_width=160,
            ),
        ).add_to(m)

    return m


def clock_str(minute: int) -> str:
    return f"{9 + minute // 60:02d}:{minute % 60:02d}"


def render():

    st.set_page_config(
        page_title="Park Heatmap",
        layout="wide",
    )

    st.markdown(
        "<h1><b><u>Park Heatmap</u></b></h1>",
        unsafe_allow_html=True,
    )

    st.caption(
        "Dot colours: 🔴 20+ min  🟠 10-19 min  🟡 5-9 min  🟢 <5 min. "
        "Click any dot for details."
    )

    header_ph = st.empty()

    cols = st.columns([3, 1])
    map_ph = cols[0].empty()
    waits_ph = cols[1].empty()

    status_ph = st.empty()

    while True:

        df = load_current()

        if df.empty:

            header_ph.warning(
                "No live data yet — start the simulator:\n\n"
                "```bash\npython run_local.py --speed 3\n```"
            )

            time.sleep(2)
            continue

        minute = int(df.park_min.iloc[0])
        total_guests = int(df.occupency.sum())
        top_wait = df.loc[df.wait_mins.idxmax()]

        with header_ph.container():

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Simulated time",
                clock_str(minute),
            )

            c2.metric(
                "Guests in rides/queues",
                total_guests,
            )

            c3.metric(
                "Longest wait",
                f"{top_wait.wait_mins:.0f} min",
                top_wait.ride_name,
            )

            c4.metric(
                "Simulated minute",
                f"{minute} / 720",
            )

        with map_ph.container():

            st_folium(
                build_map(df),
                width=1200,
                height=700,
                returned_objects=[],
                key=f"park_heatmap_{minute}",
            )

        with waits_ph.container():

            st.subheader("Longest waits")

            for r in (
                df.sort_values("wait_mins", ascending=False)
                .head(5)
                .itertuples()
            ):
                st.metric(
                    r.ride_name,
                    f"{r.wait_mins:.0f} min",
                    f"{r.occupency} guests",
                    delta_color="off",
                )

            st.divider()

            st.subheader("Walk right on")

            for r in (
                df.sort_values("wait_mins")
                .head(3)
                .itertuples()
            ):
                st.metric(
                    r.ride_name,
                    f"{r.wait_mins:.0f} min wait",
                )

        status_ph.caption(
            f"Last updated: {clock_str(minute)} — refreshing every {REFRESH_S}s"
        )

        time.sleep(REFRESH_S)


if __name__ == "__main__":
    render()