"""A classroom demonstration of streaming volume and velocity."""

import time
from datetime import datetime

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

UPDATE_INTERVAL = 0.5
MAX_ROWS = 300
HISTORY_SECONDS = 60
STATE_KEY = "simulation_v2"

st.set_page_config(page_title="Big Data Live", page_icon="📊", layout="wide")
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.volume-card {
    text-align: center; padding: 20px 12px; margin: 8px 0 20px;
    background: rgba(59, 130, 246, 0.09);
    border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 20px;
}
.volume-label { font-size: 16px; font-weight: 700; letter-spacing: 0.16em; }
.volume-number {
    font-size: clamp(48px, 8vw, 100px); font-weight: 800;
    line-height: 1.15; font-variant-numeric: tabular-nums;
}
.volume-unit { font-size: 16px; opacity: 0.7; }
</style>
""", unsafe_allow_html=True)
st.title("Big Data Live")

st.sidebar.header("Stream controls")
generation_speed = st.sidebar.slider("Events per second", 10, 1000, 200, 10)
sim_status = st.sidebar.radio("Stream", ["Running", "Paused"])
if st.sidebar.button("Reset volume & chart", width="stretch"):
    st.session_state.pop(STATE_KEY, None)


def advance_stream(state, now, next_rate):
    """Account for elapsed time at the previous rate, then apply new controls."""
    elapsed = max(0.0, now - state["updated_at"])
    incoming = state["remainder"] + elapsed * state["rate"]
    count = int(incoming)
    state["remainder"] = incoming - count
    state["total"] += count
    state["updated_at"] = now

    if count:
        # Count every event, but only materialize the bounded display buffer.
        retained = min(count, MAX_ROWS)
        batch = pd.DataFrame({
            "Time": [datetime.now()] * retained,
            "Cars": np.random.randint(2, 70, size=retained),
            "Speed (mph)": np.random.uniform(10, 75, size=retained).round(1),
        })
        state["rows"] = pd.concat(
            [state["rows"], batch], ignore_index=True
        ).tail(MAX_ROWS).reset_index(drop=True)

    seconds = now - state["started_at"]
    state["rate"] = next_rate
    state["history"].append({"Seconds": seconds, "Events per second": next_rate})
    cutoff = seconds - HISTORY_SECONDS
    # Keep one point before the window to preserve the left-edge step.
    while len(state["history"]) > 2 and state["history"][1]["Seconds"] < cutoff:
        state["history"].pop(0)
    state["history"] = state["history"][-600:]


def velocity_chart(history, seconds):
    data = pd.DataFrame(history)
    base = alt.Chart(data).encode(
        x=alt.X(
            "Seconds:Q", title="Seconds",
            scale=alt.Scale(domain=[max(0, seconds - HISTORY_SECONDS), max(10, seconds)], nice=False),
            axis=alt.Axis(format=".0f", tickCount=7, grid=False),
        ),
        y=alt.Y(
            "Events per second:Q", title="Events / second",
            scale=alt.Scale(domain=[0, 1050], nice=False),
            axis=alt.Axis(values=[0, 250, 500, 750, 1000]),
        ),
        tooltip=[alt.Tooltip("Seconds:Q", format=".1f"), "Events per second:Q"],
    )
    area = base.mark_area(interpolate="step-after", color="#3b82f6", opacity=0.2, clip=True)
    line = base.mark_line(interpolate="step-after", color="#3b82f6", strokeWidth=4, clip=True)
    latest = base.transform_filter(
        alt.datum.Seconds == data.iloc[-1]["Seconds"]
    ).mark_point(color="#3b82f6", filled=True, size=120, opacity=1)
    return (area + line + latest).properties(height=280).configure_view(
        stroke=None
    ).configure_axis(labelFontSize=13, titleFontSize=13)


@st.fragment(run_every=UPDATE_INTERVAL)
def render_dashboard():
    now = time.monotonic()
    rate = generation_speed if sim_status == "Running" else 0
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = {
            "started_at": now, "updated_at": now, "rate": rate,
            "total": 0, "remainder": 0.0,
            "rows": pd.DataFrame({
                "Time": pd.Series(dtype="datetime64[ns]"),
                "Cars": pd.Series(dtype="int64"),
                "Speed (mph)": pd.Series(dtype="float64"),
            }),
            "history": [],
        }
    state = st.session_state[STATE_KEY]
    advance_stream(state, now, rate)

    st.markdown(f"""
<div class="volume-card">
    <div class="volume-label">VOLUME</div>
    <div class="volume-number">{state['total']:,}</div>
    <div class="volume-unit">events received</div>
</div>
""", unsafe_allow_html=True)
    st.metric("VELOCITY", f"{rate:,} events / sec")
    st.progress(rate / 1000)
    st.altair_chart(
        velocity_chart(state["history"], now - state["started_at"]),
        width="stretch",
    )
    st.caption("Simulated stream · last 60 seconds")
    with st.expander("Recent sensor data"):
        st.dataframe(state["rows"].tail(8), width="stretch", hide_index=True)


render_dashboard()
