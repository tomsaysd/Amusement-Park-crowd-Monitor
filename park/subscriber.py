'''
Standard subscriber for the amusement park crowd monitor app. 
This subscriber listens to the "ride_events" topic and inserts the data into BigQuery.
'''

from google.cloud import pubsub_v1, bigquery
import json

PROJECT_ID = "amusement-park-crowd-monitor"
SUBSCRIPTION_ID = "ride_events_sub"

subscriber = pubsub_v1.SubscriberClient()
bq_client = bigquery.Client()

subscription_path = subscriber.subscription_path(
    PROJECT_ID,
    SUBSCRIPTION_ID
)

TABLE_ID = (
    "amusement-park-crowd-monitor."
    "amusement_park."
    "ride_history"
)

def callback(message):
    try:
        print("RAW:", message.data)

        data = json.loads(message.data.decode("utf-8"))

        errors = bq_client.insert_rows_json(
            TABLE_ID,
            [data]
        )

        if not errors:
            print("Inserted into BigQuery")
            message.ack()
        else:
            print(errors)
            message.ack()

    except Exception as e:
        print("ERROR:", e)
        message.ack()

print(subscription_path)
streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=callback
)

print("Listening for messages...")

streaming_pull_future.result()