'''
Standard publisher for the amusement park crowd monitor app.
This publisher takes a list of records and publishes them to the "ride-events" topic.
'''

from google.cloud import pubsub_v1
import json

PROJECT_ID = "amusement-park-crowd-monitor"
TOPIC_ID = "ride-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


def publish_records(records):
    for record in records:
        future = publisher.publish(
            topic_path,
            json.dumps(record).encode("utf-8")
        )

    return future.result()