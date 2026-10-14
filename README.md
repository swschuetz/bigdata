# Big Data Live

An interactive Streamlit classroom demonstration of **Volume**, **Velocity**, and **Value**.

## A two-minute classroom sequence

1. Start the stream. The large counter tracks all incoming events; the smaller daily number is a clearly labeled projection at the current rate.
2. Raise incoming traffic to **1,000/sec**. Animated batches become denser. Above the default **300/sec** processing capacity, the queue grows.
3. Click **Add processing capacity** to scale by 500/sec, up to 1,500/sec. Once capacity exceeds incoming traffic, the backlog drains.
4. Click **Trigger traffic jam**. New sensor readings contain slower speeds and more cars. The processed-data analytics flag congestion.
5. Trigger an incident while the queue is large to show how processing delays can delay insights. Clear the incident and watch recovery arrive through the same queue.

The chart shows 60 seconds of incoming rate, processing rate, and capacity on a fixed scale. Dots represent illustrative batches, not individual events. Pause freezes arrivals and processing; reset restores the starting controls and clears the simulation. The sensor table stays collapsed to keep the display simple.

## What is simulated

- Volume and processing budgets integrate elapsed time under the previous control settings. Each received event is either processed or waiting; events are not dropped when the display buffer fills.
- Processing is FIFO in compact cohorts. At most 128 cohorts are retained; when needed, the oldest two are combined while preserving event totals and incident proportions. Individual ordering within a combined cohort is approximated.
- Only the latest 300 processed sensor samples and at most 600 chart samples are materialized. Large event counts and queues are counters, not millions of stored Python objects.
- Normal readings have speeds of 42–68 mph; incident readings have speeds of 4–20 mph and higher car counts. Mixed, compressed cohorts are sampled proportionally. Sensor data is synthetic.
- Analytics summarize the retained processed readings. Means are per reading, not vehicle-weighted. Congestion is flagged when at least 20 readings are available and at least 60% are below 25 mph; this is a classroom rule, not a validated traffic model.
- Rates and capacity are model settings, not hardware benchmarks. Processing shows the current modeled rate: full capacity while a queue exists, otherwise the lesser of capacity and incoming traffic. Controls take effect when the server receives the change. Pausing also pauses the queue.
- The daily figure is a projection, not a claim that those events have been generated. Session data resets with a new session.

## Run locally

Use Python 3.12 or newer.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Verify the model

```sh
python -m unittest discover -s tests -v
```

Tests cover queue conservation, overload and recovery, control timing, pause/resume, incident detection and recovery, delayed alerts, and bounded memory during sustained overload.

## Deploy to Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ with GitHub access to this repository.
2. Create an app with repository `swschuetz/bigdata`, branch `main`, and main file path `app.py`.
3. Select Python 3.12 in Advanced settings, then deploy.

Keep `app.py`, `simulation.py`, `style.css`, and `requirements.txt` together. No API keys, secrets, or external data services are required.
