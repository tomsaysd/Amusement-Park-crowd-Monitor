# Amusement Park Crowd Monitor — (Cloud POC)

A proof-of-concept Streamlit app designed for guests to view info about ride congestions or
other miscellaneous information about the park.   
The crowd data is produced
by an **agent-based simulation** (not random numbers), so movement looks
natural: a calm open, a midday peak, gradual queue build-up, and crowds that
spill from one zone into neighbouring ones.<br><br>
Currently there are two features implemented:<br><br>
A crowd heatmap for each ride, and a ride queue time predictor.

## How to run:
Install the folder and activate your virtual environment (if applicable).  
To run the program, use:
```bash
#Install all dependencies (without or without venv) with:
pip install -r requirements.txt


# To run the local version that writes crowd data to local sqlite file:
python run_local.py         
# You can toggle speed by appending "--speed x"
# x=3 is recommended for readable fast updates.

# To run the streamlit app landing page:
streamlit run home.py
# You MUST run this streamlit app only after the local version, since the sqlite reference is required.
```


## Architecture (for when we go to the cloud)

Simulated guests move around the park → each crowd reading is published once →
it fans out to a fast store for the **live heatmap** and a warehouse for
**analytics/predictions** → the app reads both.

| Stage | Service | Why it's here | File |
|------|---------|---------------|------|
| Trigger | Cloud Scheduler | Advances the sim clock on a timer | (console config) |
| Data source | Cloud Run | Runs the simulator, publishes readings | `cloud/publisher.py` |
| Transport | Pub/Sub | One message → different concerns (fanout) | (topic + multiple subs) |
| Database | BigQuery | Stores every reading; trend/prediction queries | `cloud/bigquery_setup.sql` |
| App | Cloud Run | Primary app features display | `home.py` |


## Tuning the simulation

In `simulator.py`, the `Simulation` constructor exposes the knobs:
`attendance_scale` (total crowd, ≈3,600 concurrent at the default 30),
`wait_aversion` (how hard guests dodge lines), `distance_scale` (how far they
roam), and `seed` (reproducibility).