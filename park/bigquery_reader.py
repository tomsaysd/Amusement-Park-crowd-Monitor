from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "amusement-park-crowd-monitor"
DATASET = "amusement_park"
TABLE = "ride_history"

client = bigquery.Client()


def load_history():
    query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    """

    return client.query(query).to_dataframe()