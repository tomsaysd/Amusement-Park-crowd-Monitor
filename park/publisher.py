"""
One-shot simulator run for the Cloud Run Job.
Runs a single day (minute 0 to 720), publishing each minute's readings to
Pub/Sub, then exits. Cloud Scheduler is responsible for triggering this
Job again to produce the next "day" -- this script does NOT loop itself.
"""

import os
import time

from simulator import Simulation
from pubsub_publisher import publish_records

TICK_SECONDS = 1.0 / float(os.environ.get("SPEED", "1"))


def main():
    sim = Simulation(seed=int(os.environ.get("SEED", "7")))
    print(f"Starting one-shot run (speed={os.environ.get('SPEED', '1')})")

    while sim.minute <= 720:
        records = sim.step()
        publish_records(records)
        print(f"published minute {sim.minute - 1}")
        time.sleep(TICK_SECONDS)

    print("Run complete, exiting.")


if __name__ == "__main__":
    main()