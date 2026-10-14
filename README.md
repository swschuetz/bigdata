# Big Data Live

A Streamlit classroom simulation focused on **Volume**, **Velocity**, and the **Value** of live analytics.

- A large central counter shows accumulated events.
- Move the 10–1,000 events/second slider to change the incoming rate.
- The velocity chart retains its own 60-second history on a fixed vertical scale, so rate changes remain visible even as sensor rows leave the display buffer.
- Three compact analytics cards show mean speed, the percentage of readings below 25 mph, and mean cars per reading, calculated from the latest available sensor rows (up to 300). Means are per reading, not vehicle-weighted.
- Pause stops accumulation and shows zero velocity while retaining the traffic snapshot; reset clears volume, chart history, and analytics.
- Recent sensor readings are available in a collapsed panel. JSON logs are removed.

The counter integrates elapsed time at the selected simulated rate. It is not a benchmark of real ingestion throughput. Only the latest 300 sensor rows and at most 600 chart samples are retained in memory. Session data resets when a new session starts.

## Run locally

Use Python 3.12 or newer.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ with GitHub access to this repository.
2. Create an app with repository `swschuetz/bigdata`, branch `main`, and main file path `app.py`.
3. Select Python 3.12 in Advanced settings, then deploy.

Dependencies are installed from `requirements.txt`. No API keys, secrets, or external data services are required.
