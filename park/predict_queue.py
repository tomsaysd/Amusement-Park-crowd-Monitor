"""
The queue-time prediction logic, kept separate from UI so it can be tested
on its own and reused.
"""

import sqlite3
import pandas as pd


def hour_from_minute(park_min: int) -> int:
    return 9 + park_min // 60


def load_history(db_path="park_data.sqlite") -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM ride_history", con)
    con.close()
    if df.empty:
        return df
    df["hour"] = 9 + df["park_min"] // 60
    return df


def predicted_wait_by_hour(history: pd.DataFrame) -> pd.DataFrame:
    """Average wait per ride per hour -- the core prediction table.
    In BigQuery this is literally:
        SELECT ride_name, EXTRACT(HOUR FROM timestamp) hour,
               AVG(wait_mins) predicted_wait
        FROM ride_history GROUP BY ride_name, hour
    """
    return (history.groupby(["ride_name", "hour"])["wait_mins"]
                   .mean().reset_index()
                   .rename(columns={"wait_mins": "predicted_wait"}))


def predict(history: pd.DataFrame, ride_name: str, hour: int) -> float | None:
    """Predicted wait for one ride at one hour."""
    tbl = predicted_wait_by_hour(history)
    row = tbl[(tbl.ride_name == ride_name) & (tbl.hour == hour)]
    return None if row.empty else float(row.predicted_wait.iloc[0])


def best_time(history: pd.DataFrame, ride_name: str) -> tuple[int, float] | None:
    """The hour with the shortest predicted wait (ignoring before-open/after-close
    hours where the park is empty)."""
    tbl = predicted_wait_by_hour(history)
    tbl = tbl[(tbl.ride_name == ride_name) & (tbl.predicted_wait > 0.5)]
    if tbl.empty:
        return None
    row = tbl.loc[tbl.predicted_wait.idxmin()]
    return int(row.hour), float(row.predicted_wait)


if __name__ == "__main__":
    h = load_history()
    if h.empty:
        print("No history yet -- run run_local.py first.")
    else:
        print(f"History rows: {len(h):,}")
        p = predict(h, "Galaxy Coaster", 14)
        print(f"Predicted Galaxy Coaster wait at 14:00 -> {p:.1f} min")
        bt = best_time(h, "Galaxy Coaster")
        print(f"Best time for Galaxy Coaster -> {bt[0]:02d}:00 ({bt[1]:.1f} min)")