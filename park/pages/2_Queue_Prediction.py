"""

Second page of the Streamlit app: predicts ride queue times by hour, from the
historical readings in ride_history. 

The prediction is the historical average wait for each ride at each hour --
taken from predict_queue.py
"""

import altair as alt
import pandas as pd
import streamlit as st

from predict_queue import load_history, predicted_wait_by_hour, best_time


def wait_band(mins: float) -> str:
    if mins >= 20: return "Very busy"
    if mins >= 10: return "Busy"
    if mins >= 5:  return "Moderate"
    return "Quiet"


st.set_page_config(page_title="Queue prediction", layout="wide")
st.markdown("<h1><b><u>Ride Queue-Time Prediction</u></b></h1>", unsafe_allow_html=True)
st.caption("Predicted wait by hour, based on historical crowd patterns.")

history = load_history()

if history.empty:
    st.warning(
        "No history yet. Run the simulator to build some:\n\n"
        "```\npython run_local.py --speed 30\n```\n\n"
        "Let it run through a full day or two, then reload this page."
    )
    st.stop()

days = history["timestamp"].dt.date.nunique() if "timestamp" in history else 1
st.caption(f"Trained on {len(history):,} readings across ~{days} simulated day(s).")

rides = sorted(history.ride_name.unique())
ride = st.selectbox("Choose a ride", rides,
                    index=rides.index("Galaxy Coaster") if "Galaxy Coaster" in rides else 0)

tbl = predicted_wait_by_hour(history)
ride_tbl = tbl[tbl.ride_name == ride].sort_values("hour").copy()
ride_tbl["clock"] = ride_tbl.hour.apply(lambda h: f"{h:02d}:00")
ride_tbl["status"] = ride_tbl.predicted_wait.apply(wait_band)

# --- HEADLINE RECOMMENDATION ---
bt = best_time(history, ride)
peak = ride_tbl.loc[ride_tbl.predicted_wait.idxmax()]
c1, c2 = st.columns(2)
if bt:
    c1.metric("Best time to ride", f"{bt[0]:02d}:00", f"~{bt[1]:.0f} min wait",
              delta_color="off")
c2.metric("Worst time to ride", peak.clock, f"~{peak.predicted_wait:.0f} min wait",
          delta_color="inverse")

st.divider()

# --- PREDICTED WAIT TIME BAR CHART ---
chart = (
    alt.Chart(ride_tbl)
    .mark_bar(cornerRadius=3)
    .encode(
        x=alt.X("clock:N", title="hour of day", sort=None),
        y=alt.Y("predicted_wait:Q", title="predicted wait (min)"),
        color=alt.Color("predicted_wait:Q",
                        scale=alt.Scale(scheme="yelloworangered"),
                        legend=None),
        tooltip=["clock", alt.Tooltip("predicted_wait:Q", format=".1f"), "status"],
    )
    .properties(height=320)
)
st.altair_chart(chart, use_container_width=True)

# --- VISIT PLANNING USER SLIDER ---
st.subheader("Plan a visit")
hours = ride_tbl.clock.tolist()
chosen = st.select_slider("If I arrive at...", options=hours,
                          value=hours[len(hours)//2])
row = ride_tbl[ride_tbl.clock == chosen].iloc[0]
st.info(f"**{ride}** at **{chosen}** — expect about "
        f"**{row.predicted_wait:.0f} min** wait ({row.status.lower()}).")