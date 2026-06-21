from google.cloud import pubsub_v1

project_id = "amusement-park-crowd-monitor"
topic_id = "ride_events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

future = publisher.publish(
    topic_path,
    b"Hello from Tom!"
)

print(f"Published message ID: {future.result()}")