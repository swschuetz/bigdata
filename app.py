"""A live Streamlit demonstration of Big Data in an IoT smart city."""

import json
import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

UPDATE_INTERVAL = 0.5
MAX_ROWS = 300
MAX_LOGS = 8

st.set_page_config(
    page_title="Live Big Data Simulation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Real-Time Big Data Classroom Demonstration")
st.markdown("""
This live dashboard simulates an enterprise **IoT Smart City Sensor Network**.
Use this to demonstrate the core pillars of Big Data
(**Volume, Velocity, Variety, and Value**) in real time.
""")

if "traffic_data" not in st.session_state:
    now = time.time()
    st.session_state.traffic_data = pd.DataFrame({
        "Timestamp": [datetime.fromtimestamp(now - i) for i in range(50, 0, -1)],
        "Car_Count": np.random.randint(5, 45, size=50),
        "Avg_Speed_MPH": np.random.uniform(25, 60, size=50),
        "DataType": ["Structured"] * 50,
    })
    st.session_state.total_rows_processed = 50
    st.session_state.raw_log_stream = []

st.sidebar.header("🕹️ Live Lecture Controls")
st.sidebar.markdown("Adjust these live to show how systems scale under load.")
generation_speed = st.sidebar.slider(
    "⚡ Velocity (Sensor Packets / Second)",
    min_value=10,
    max_value=1000,
    value=200,
    step=10,
)
sim_status = st.sidebar.radio("Simulator Status", ["Running", "Paused"])
st.sidebar.markdown("---")
st.sidebar.info("""
💡 **Classroom Tip:**
Crank the slider to 1,000/sec to show students how quickly **Volume**
accumulates, then point to the semi-structured JSON logs to explain **Variety**.
""")
st.sidebar.caption(
    "The selected rate is simulated in half-second batches, plus system logs. "
    "Actual throughput depends on rendering speed. Only the latest 300 sensor "
    "rows and 8 logs are retained; accumulated volume counts all events."
)


def generate_batch():
    """Append one bounded batch of sensor readings and JSON system logs."""
    batch_size = max(1, int(generation_speed * UPDATE_INTERVAL))
    new_structured_batch = pd.DataFrame({
        "Timestamp": [datetime.now()] * batch_size,
        "Car_Count": np.random.randint(2, 70, size=batch_size),
        "Avg_Speed_MPH": np.random.uniform(10, 75, size=batch_size),
        "DataType": ["Structured"] * batch_size,
    })

    new_logs = []
    log_id_base = time.time_ns()
    for i in range(min(5, max(1, int(batch_size * 0.05)))):
        log_packet = {
            "log_id": log_id_base + i,
            "level": str(np.random.choice(
                ["INFO", "WARNING", "ERROR"], p=[0.8, 0.15, 0.05]
            )),
            "message": (
                f"Sensor_{np.random.randint(100, 999)} "
                "pinged network gateway successfully."
            ),
            "raw_payload_bytes": int(np.random.randint(128, 1024)),
        }
        new_logs.append(json.dumps(log_packet))

    st.session_state.traffic_data = pd.concat(
        [st.session_state.traffic_data, new_structured_batch], ignore_index=True
    ).tail(MAX_ROWS).reset_index(drop=True)
    st.session_state.raw_log_stream = (
        st.session_state.raw_log_stream + new_logs
    )[-MAX_LOGS:]
    st.session_state.total_rows_processed += batch_size + len(new_logs)


@st.fragment(run_every=UPDATE_INTERVAL if sim_status == "Running" else None)
def render_dashboard():
    """Refresh the live view while preserving the display when paused."""
    if sim_status == "Running":
        generate_batch()

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "📦 Accumulated Volume",
        f"{st.session_state.total_rows_processed:,} events",
    )
    active_speed = generation_speed if sim_status == "Running" else 0
    col2.metric(
        "⚡ Simulated Sensor Velocity",
        f"{active_speed:,} packets/sec",
        delta=f"{active_speed * 60:,} packets/min",
    )
    col3.metric("🌈 Data Variety", "2 Stream Types", delta="Tabular + Raw JSON")

    st.markdown("### 📈 Live Analytics View (Value)")
    chart_df = st.session_state.traffic_data.copy()
    chart_df["Time"] = chart_df["Timestamp"].dt.floor("s")
    summary_df = chart_df.groupby("Time")[["Car_Count"]].sum().tail(15)
    st.line_chart(summary_df, height=250)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 🗂️ Structured Storage Data (Rows)")
        st.dataframe(
            st.session_state.traffic_data.tail(8)[
                ["Timestamp", "Car_Count", "Avg_Speed_MPH"]
            ],
            width="stretch",
            hide_index=True,
        )
    with col_right:
        st.markdown("### 🪵 Semi-Structured JSON Log Firehose")
        st.code("\n".join(st.session_state.raw_log_stream), language="json")


render_dashboard()
