"""Interactive classroom demonstration of a streaming data pipeline."""

import math
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from simulation import HISTORY_SECONDS, Simulation

UPDATE_INTERVAL = 0.5
STATE_KEY = "simulation_v3"
MAX_CAPACITY = 1500

st.set_page_config(page_title="Big Data Live", page_icon="📊", layout="wide")
st.html(Path(__file__).with_name("style.css"))
st.title("Big Data Live")


def reset_simulation():
    st.session_state.pop(STATE_KEY, None)
    st.session_state.update(arrival_rate=200, capacity=300, traffic_jam=False, stream_status="Running")


def add_capacity():
    st.session_state.capacity = min(MAX_CAPACITY, st.session_state.capacity + 500)


def toggle_jam():
    st.session_state.traffic_jam = not st.session_state.traffic_jam


for key, value in {"arrival_rate": 200, "capacity": 300, "traffic_jam": False, "stream_status": "Running"}.items():
    st.session_state.setdefault(key, value)

st.sidebar.header("Stream controls")
st.sidebar.slider("Incoming events / sec", 10, 1000, step=10, key="arrival_rate")
st.sidebar.radio("Simulation", ["Running", "Paused"], key="stream_status")
st.sidebar.divider()
st.sidebar.slider("Processing capacity / sec", 100, MAX_CAPACITY, step=100, key="capacity")
st.sidebar.button(
    "Add processing capacity", on_click=add_capacity, width="stretch",
    disabled=st.session_state.capacity >= MAX_CAPACITY,
)
st.sidebar.button(
    "Clear traffic jam" if st.session_state.traffic_jam else "Trigger traffic jam",
    on_click=toggle_jam, type="primary", width="stretch",
)
if st.session_state.traffic_jam:
    st.sidebar.caption("Traffic jam active")
st.sidebar.divider()
st.sidebar.button("Reset simulation", on_click=reset_simulation, width="stretch")


def flow_lane(rate, seconds, outgoing=False):
    # Dots are illustrative event batches, not one dot per event.
    count = min(30, math.ceil(rate / 40)) if rate else 0
    duration = 3.6 - min(rate, MAX_CAPACITY) / MAX_CAPACITY * 2
    dots = "".join(
        f'<span class="flow-dot" style="animation-duration:{duration:.3f}s;'
        f'animation-delay:-{(seconds + i * duration / count) % duration:.3f}s"></span>'
        for i in range(count)
    )
    return f'<div class="flow-lane {"outgoing" if outgoing else "incoming"}" aria-hidden="true">{dots}</div>'


def render_flow(sim):
    queue_class = "overloaded" if sim.backlog else ""
    st.html(f"""
<div class="pipeline" role="img" aria-label="Simulated event batches flow from sensors through processing to insights">
  <div class="flow-stage">Sensors<span>{'Traffic jam' if sim.jam else 'Smart city'}</span></div>
  {flow_lane(sim.incoming_rate, sim.active_seconds)}
  <div class="flow-stage {queue_class}">Processing<span>{sim.capacity:,}/sec capacity</span></div>
  {flow_lane(sim.processing_rate, sim.active_seconds, outgoing=True)}
  <div class="flow-stage">Insights<span>Live analytics</span></div>
</div>
""")


def velocity_chart(sim):
    seconds = sim.history[-1]["Seconds"]
    data = pd.DataFrame(sim.history)
    x = alt.X(
        "Seconds:Q", title="Seconds",
        scale=alt.Scale(domain=[max(0, seconds - HISTORY_SECONDS), max(10, seconds)], nice=False),
        axis=alt.Axis(format=".0f", tickCount=7, grid=False),
    )
    scale = alt.Scale(domain=[0, 1600], nice=False)
    base = alt.Chart(data).encode(x=x)
    area = base.mark_area(interpolate="step-after", color="#3b82f6", opacity=0.10, clip=True).encode(
        y=alt.Y("Incoming:Q", title="Events / sec", scale=scale, axis=alt.Axis(values=[0, 500, 1000, 1500], labelOverlap=False)),
    )
    lines = base.transform_fold(["Incoming", "Processing", "Capacity"], as_=["Stream", "Rate"]).encode(
        y=alt.Y("Rate:Q", title="Events / sec", scale=scale, axis=alt.Axis(values=[0, 500, 1000, 1500], labelOverlap=False)),
        color=alt.Color("Stream:N", scale=alt.Scale(
            domain=["Incoming", "Processing", "Capacity"],
            range=["#3b82f6", "#10b981", "#f59e0b"],
        ), legend=alt.Legend(title=None, orient="top", labelFontSize=12)),
        strokeDash=alt.StrokeDash("Stream:N", scale=alt.Scale(
            domain=["Incoming", "Processing", "Capacity"], range=[[1, 0], [1, 0], [6, 4]]
        ), legend=None),
        tooltip=[alt.Tooltip("Seconds:Q", format=".1f"), "Stream:N", "Rate:Q"],
    )
    paths = lines.mark_line(interpolate="step-after", strokeWidth=3, clip=True)
    latest = lines.transform_filter(alt.datum.Seconds == seconds).mark_point(filled=True, size=60)
    return (area + paths + latest).properties(height=260).configure_view(stroke=None)


def render_analytics(sim):
    snapshot = sim.analytics()
    if sim.backlog:
        st.warning("Analytics delayed · showing older traffic conditions", icon="⏳")
        if snapshot and snapshot["congestion"]:
            st.caption("Congestion detected in the processed readings.")
    elif not sim.running:
        st.info("Analytics paused · showing last processed readings", icon="⏸️")
        if snapshot and snapshot["congestion"]:
            st.caption("Congestion detected in the last processed readings.")
    elif snapshot and snapshot["congestion"]:
        st.warning("Congestion detected · consider rerouting traffic", icon="🚦")
    elif len(sim.rows) >= 20:
        st.success("Traffic flowing · no congestion detected", icon="✅")
    else:
        st.info("Waiting for processed sensor readings", icon="📡")
    speed_col, slow_col, cars_col = st.columns(3)
    speed_col.metric("Average speed", f"{snapshot['speed']:.1f} mph" if snapshot else "—", border=True)
    slow_col.metric("Slow readings (<25 mph)", f"{snapshot['slow_share']:.0%}" if snapshot else "—", border=True)
    cars_col.metric("Cars / reading", f"{snapshot['cars']:.1f}" if snapshot else "—", border=True)
    st.caption(f"Latest {len(sim.rows):,} processed readings · alerts follow the data through the queue")
    with st.expander("Recent sensor data"):
        st.dataframe(pd.DataFrame(list(sim.rows)[-8:]), width="stretch", hide_index=True)


@st.fragment(run_every=UPDATE_INTERVAL)
def render_dashboard():
    now = time.monotonic()
    controls = dict(
        rate=st.session_state.arrival_rate, capacity=st.session_state.capacity,
        jam=st.session_state.traffic_jam, running=st.session_state.stream_status == "Running",
    )
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = Simulation(now, **controls)
    sim = st.session_state[STATE_KEY]
    sim.advance(now, **controls)

    st.html(f"""
<div class="volume-card">
  <div class="volume-label">VOLUME</div>
  <div class="volume-number">{sim.total:,}</div>
  <div class="volume-unit">events received</div>
  <div class="volume-projection">{sim.incoming_rate * 86400:,} events / day at this rate <span>· projection</span></div>
</div>
""")
    render_flow(sim)
    incoming, processing, backlog = st.columns(3)
    incoming.metric("Incoming / sec", f"{sim.incoming_rate:,}")
    processing.metric("Processing / sec", f"{sim.processing_rate:,}")
    queue_label = "Backlog · paused" if not sim.running else (
        "Backlog · growing" if sim.incoming_rate > sim.capacity else
        "Backlog · catching up" if sim.backlog and sim.capacity > sim.rate else
        "Backlog · waiting" if sim.backlog else "Backlog · clear"
    )
    backlog.metric(
        queue_label, f"{sim.backlog:,}",
        help="New-reading wait is backlog divided by processing capacity, assuming "
             "capacity stays constant. It estimates when a new reading reaches "
             "processing, not when the entire queue empties or an alert fires.",
    )
    wait_label = f"≈{math.ceil(sim.backlog / sim.capacity):,} s" if sim.running else "paused"
    backlog.caption(f"New-reading wait: {wait_label}")
    st.altair_chart(velocity_chart(sim), width="stretch")
    st.caption("Simulated rates · last 60 seconds · moving dots represent event batches")
    render_analytics(sim)


render_dashboard()
