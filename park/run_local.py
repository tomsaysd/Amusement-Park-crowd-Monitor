"""
Runs the simulation live, one minute at a time, writing each minute's readings
into an SQLite file. Leave this running in one terminal; Every time the app 
refreshes it reads the latest minute from the database, which this script keeps
advancing.

simulation speed can be adjusted by appending "--speed x" to the command,
where 'x' represents number of simulated minutes per second.
"""

import argparse
import sqlite3
import time

import pandas as pd

from simulator import Simulation


DB_PATH = "park_data.sqlite"


def init_db(con: sqlite3.Connection):
    """Create (or reset) the live_status table that the app reads, and the
    history table that BigQuery will eventually replace."""
    con.executescript("""
        DROP TABLE IF EXISTS live_status;
        CREATE TABLE live_status (
            ride_id          TEXT PRIMARY KEY,
            ride_name        TEXT,
            zone_id          TEXT,
            x                REAL,
            y                REAL,
            queue_length     INTEGER,
            riders           INTEGER,
            occupancy        INTEGER,
            wait_minutes     REAL,
            park_minute      INTEGER,
            timestamp        TEXT
        );

        CREATE TABLE IF NOT EXISTS ride_history (
            timestamp        TEXT,
            park_minute      INTEGER,
            zone_id          TEXT,
            ride_id          TEXT,
            ride_name        TEXT,
            x                REAL,
            y                REAL,
            queue_length     INTEGER,
            riders           INTEGER,
            occupancy        INTEGER,
            wait_minutes     REAL,
            throughput_per_min INTEGER
        );
    """)
    con.commit()


def write_minute(con: sqlite3.Connection, records: list[dict]):
    """Upsert the latest readings into live_status (the app reads this) and
    append them to ride_history (the analytics / BigQuery stand-in)."""
    for r in records:
        con.execute("""
            INSERT INTO live_status VALUES
                (:ride_id, :ride_name, :zone_id, :x, :y,
                 :queue_length, :riders, :occupancy, :wait_minutes,
                 :park_minute, :timestamp)
            ON CONFLICT(ride_id) DO UPDATE SET
                queue_length  = excluded.queue_length,
                riders        = excluded.riders,
                occupancy     = excluded.occupancy,
                wait_minutes  = excluded.wait_minutes,
                park_minute   = excluded.park_minute,
                timestamp     = excluded.timestamp
        """, r)
    pd.DataFrame(records).to_sql(
        "ride_history", con, if_exists="append", index=False)
    con.commit()


def clock_str(minute: int) -> str:
    h = 9 + minute // 60
    m = minute % 60
    return f"{h:02d}:{m:02d}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Simulated minutes advanced per real second (default 1)")
    parser.add_argument("--seed", type=int, default=7,
                        help="Random seed — change this for a different day")
    args = parser.parse_args()

    sleep_s = 1.0 / args.speed

    con = sqlite3.connect(DB_PATH)
    init_db(con)

    sim = Simulation(seed=args.seed)
    total = 721  # minutes 0..720

    print(f"Simulator started  (seed={args.seed}, speed={args.speed}x)")
    print(f"Park opens at 09:00, closes at 21:00 ({total} minutes total)")
    print(f"Speed {args.speed}x means one simulated minute every {sleep_s:.2f}s")
    print(f"Full day will complete in ~{total * sleep_s / 60:.1f} real minutes")
    print("─" * 52)

    while sim.minute <= 720:
        records = sim.step()
        write_minute(con, records)

        total_occ = sum(r["occupancy"] for r in records)
        top = max(records, key=lambda r: r["wait_minutes"])
        print(
            f"  {clock_str(sim.minute - 1)}  "
            f"guests in rides/queues: {total_occ:>4}  "
            f"longest wait: {top['ride_name']} {top['wait_minutes']:.0f}min"
        )

        time.sleep(sleep_s)

    con.close()
    print("─" * 52)
    print("Park closed. Full day written to ride_history.")
    print("Run again (--seed N) for a different day.")


if __name__ == "__main__":
    main()