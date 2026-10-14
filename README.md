# Live Big Data Simulation

A Streamlit classroom dashboard simulating an IoT smart city sensor network to illustrate Volume, Velocity, Variety, and Value.

## Run locally

Use Python 3.12 or newer.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Adjust the sidebar velocity slider or pause/resume the simulation. Sensor rows and semi-structured JSON logs refresh every half-second while running. The selected velocity is a simulated target; actual throughput depends on rendering speed. Volume includes sensor packets and additional logs. Memory is bounded to the latest 300 sensor rows and 8 log entries, while the cumulative event count continues increasing. Session data resets when a new session starts.

## Deploy to Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ with GitHub access to this repository.
2. Create an app with repository `swschuetz/bigdata`, branch `main`, and main file path `app.py`.
3. Select Python 3.12 in Advanced settings, then deploy.

Dependencies are installed from `requirements.txt`. No API keys, secrets, or external data services are required.

Deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
