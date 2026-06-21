"""
Landing page for the Park Crowd Monitor app.
"""

import sqlite3

import streamlit as st

DB_PATH = "park_data.sqlite"

st.set_page_config(page_title="Park Crowd Monitor", page_icon="🎡",
                   layout="wide")


def data_status() -> str:
    """A small live/!live indicator so the landing page tells you whether the
    simulator is feeding data before you click into a feature."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.execute("SELECT MAX(park_min) FROM live_status")
        minute = cur.fetchone()[0]
        con.close()
        if minute is None:
            return "no-data"
        return f"live (minute {minute})"
    except Exception:
        return "no-data"


st.markdown("<h1><b>AMUSEMENT PARK CROWD MONITOR</b></h1>", unsafe_allow_html=True)
st.markdown("<h2><i>A simulated crowd-intelligence app for an amusement park</i></h2>", unsafe_allow_html=True)

st.write(
    "This app turns a live simulation of guests moving around the park into two "
    "things visitors care about: how busy each area currently is, and how long "
    "the wait for a ride is likely to be at a given hour of the day."
)

# --- DATA STATUS BANNER ---
status = data_status()
if status == "no-data":
    st.warning(
        "No live data yet. Start the simulator in a separate terminal:\n\n"
        "```\npython run_local.py --speed 30\n```\n\n"
        "Then use the sidebar to open a feature."
    )
else:
    st.success(f"Simulator data retrieved! — data is {status}.")

st.divider()

# --- TOOL LINKS ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Park heatmap")
    st.write(
        "A live overhead map of the park with a heat overlay showing where the "
        "crowds are right now, plus current wait times per ride."
    )
    try:
        st.page_link("pages/1_Park_Heatmap.py", label="Open the heatmap",
                     icon="🗺️")
    except Exception:
        st.write("Open **Park Heatmap** from the sidebar.")

with col2:
    st.markdown("### Queue prediction")
    st.write(
        "Predicted wait times for each ride across the day, learned from "
        "historical crowd patterns, with a best-time-to-ride recommendation."
    )
    try:
        st.page_link("pages/2_Queue_Prediction.py", label="Open the predictor",
                     icon="📈")
    except Exception:
        st.write("Open **Queue Prediction** from the sidebar.")

st.divider()
st.caption(
    "Built on a Pub/Sub + BigQuery pipeline; this Streamlit app is the "
    "user-facing layer, deployed as a single container on Cloud Run."
)