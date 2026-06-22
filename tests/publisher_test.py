'''
Isolated test for pubsub publisher. 
Publishes a single JSON message to the "ride-events" topic.
'''

from google.cloud import pubsub_v1
import json

project_id = "amusement-park-crowd-monitor"
topic_id = "ride_events"

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    project_id,
    topic_id
)

data = {
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
print(topic_path)
future = publisher.publish(
    topic_path,
    json.dumps(data).encode("utf-8")
)

print("Message ID:", future.result())


print("Published")