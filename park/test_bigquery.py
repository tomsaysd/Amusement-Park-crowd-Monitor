from google.cloud import bigquery

client = bigquery.Client()

table_id = "amusement-park-crowd-monitor.amusement_park.ride_history"

rows = [
    {
        "timestamp": "2026-01-01T12:00:00",
        "park_min": 1,
        "zone_id": "A",
        "ride_id": "R1",
        "ride_name": "Roller Coaster",
        "x": 10.0,
        "y": 20.0,
        "queue_length": 15,
        "riders": 100,
        "occupency": 80,
        "wait_mins": 12.5,
        "throughput_per_min": 5
    }
]

errors = client.insert_rows_json(table_id, rows)

if not errors:
    print("Data inserted successfully!")
else:
    print(errors)