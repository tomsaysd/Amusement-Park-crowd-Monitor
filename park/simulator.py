"""
An *agent-based* simulation: instead of assigning new locations
each tick (which looks like teleporting guests),this file simulates individual 
guests that arrive, walk between rides, queue, ride, and eventually leave. 

The crowd at any ride is simply "how many guests are there right now." 
Each tick is one simulated minute.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from park import RIDES, RIDE_BY_ID, RIDES_IN_ZONE, ZONES, walk_minutes


OPEN_MINUTE = 0           # 09:00
CLOSE_MINUTE = 720        # 21:00 (12 hour total day)
PARK_OPEN_CLOCK = datetime(2025, 6, 1, 9, 0, tzinfo=timezone.utc)


class State(Enum):
    WALKING = "walking" 
    QUEUING = "queuing"
    RIDING = "riding"
    LEFT = "left"


@dataclass
class Agent:
    agent_id: int
    location: str                 # ride_id the agent is at / heading to
    state: State
    timer: float = 0.0            # minutes remaining in current state
    rides_done: int = 0
    planned_rides: int = 8        # roughly how many rides before heading home
    last_ride: str | None = None  # avoid immediately re-riding the same thing


def arrival_mean(minute: int, scale: float) -> float:
    """Expected number of new guests arriving this minute. A mixture of two
    bumps: a strong late-morning surge and a softer afternoon wave, tapering
    to nothing before close. `scale` tunes total daily attendance."""
    morning = math.exp(-((minute - 130) ** 2) / (2 * 75 ** 2))
    afternoon = 0.55 * math.exp(-((minute - 320) ** 2) / (2 * 120 ** 2))
    rate = scale * (morning + afternoon)
    if minute > 560:          # very few new arrivals in the last ~2.5 hours
        rate *= 0.15
    return rate


class Simulation:
    def __init__(self, seed: int = 7, attendance_scale: float = 30.0,
                 wait_aversion: float = 25.0, distance_scale: float = 35.0):
        self.rng = random.Random(seed)
        self.attendance_scale = attendance_scale
        self.wait_aversion = wait_aversion      # higher => guests dodge lines harder
        self.distance_scale = distance_scale    # higher => guests roam further
        self.minute = 0
        self._next_id = 0

        self.agents: dict[int, Agent] = {}
        # Per-ride live state:
        self.queue: dict[str, list[int]] = {r.ride_id: [] for r in RIDES}
        self.riding: dict[str, list[int]] = {r.ride_id: [] for r in RIDES}

    def _choose_ride(self, agent: Agent) -> str:
        """Pick the next ride. Weight = popularity x (closeness) x (short line).
        Sampled, not maximised, so behaviour is varied but not random noise."""
        here = RIDE_BY_ID[agent.location]
        weights, ids = [], []
        for r in RIDES:
            if r.ride_id == agent.last_ride:
                continue
            wait = len(self.queue[r.ride_id]) / r.throughput_per_min
            dist = walk_minutes(here, r)
            w = (r.popularity
                 * math.exp(-dist / self.distance_scale)
                 * math.exp(-wait / self.wait_aversion))
            weights.append(w)
            ids.append(r.ride_id)
        return self.rng.choices(ids, weights=weights, k=1)[0]

    def _spawn_arrivals(self):
        entrance = RIDE_BY_ID["carousel"]
        n = self._poisson(arrival_mean(self.minute, self.attendance_scale))
        for _ in range(n):
            a = Agent(agent_id=self._next_id, location=entrance.ride_id,
                      state=State.WALKING, planned_rides=self.rng.randint(5, 12))
            target = self._choose_ride(a)
            a.location = target
            a.timer = walk_minutes(entrance, RIDE_BY_ID[target])
            self.agents[a.agent_id] = a
            self._next_id += 1

    def _poisson(self, lam: float) -> int:
        # Knuth's algorithm; lam is small here so this is cheap.
        if lam <= 0:
            return 0
        L, k, p = math.exp(-lam), 0, 1.0
        while True:
            k += 1
            p *= self.rng.random()
            if p <= L:
                return k - 1

    def step(self) -> list[dict]:
        '''Advance the simulation by one minute, updating agent states and emitting
        a record for each ride with current queue length, riders, and wait time.'''
        if self.minute < 560:
            self._spawn_arrivals()

        # 1. Load guests from each queue onto each ride, up to throughput.
        for r in RIDES:
            seats = r.throughput_per_min
            q = self.queue[r.ride_id]
            boarding, q[:] = q[:seats], q[seats:]
            for aid in boarding:
                a = self.agents[aid]
                a.state = State.RIDING
                a.timer = r.duration_min
                self.riding[r.ride_id].append(aid)

        # 2. Advance everyone who is riding or walking.
        finished_riding: list[int] = []
        for aid, a in self.agents.items():
            if a.state is State.RIDING:
                a.timer -= 1
                if a.timer <= 0:
                    finished_riding.append(aid)
            elif a.state is State.WALKING:
                a.timer -= 1
                if a.timer <= 0:
                    a.state = State.QUEUING
                    self.queue[a.location].append(aid)

        # 3. Riders who just finished decide what to do next.
        for aid in finished_riding:
            a = self.agents[aid]
            self.riding[a.last_ride or a.location]  # noqa (clarity)
            # remove from whichever riding list holds it
            for r in RIDES:
                if aid in self.riding[r.ride_id]:
                    self.riding[r.ride_id].remove(aid)
                    a.last_ride = r.ride_id
                    break
            a.rides_done += 1
            leave = (a.rides_done >= a.planned_rides) or (self.minute > 650)
            if leave:
                a.state = State.LEFT
            else:
                target = self._choose_ride(a)
                a.state = State.WALKING
                a.timer = walk_minutes(RIDE_BY_ID[a.last_ride], RIDE_BY_ID[target])
                a.location = target

        # 4. Emit one data record per ride for this minute.
        clock = PARK_OPEN_CLOCK + timedelta(minutes=self.minute)
        records = []
        for r in RIDES:
            qlen = len(self.queue[r.ride_id])
            riders = len(self.riding[r.ride_id])
            wait = round(qlen / r.throughput_per_min, 1)
            records.append({
                "timestamp": clock.isoformat(),
                "park_min": self.minute,
                "zone_id": r.zone_id,
                "ride_id": r.ride_id,
                "ride_name": r.name,
                "x": r.x, "y": r.y,
                "queue_length": qlen,
                "riders": riders,
                "occupency": qlen + riders,         # how crowded this ride is
                "wait_mins": wait,
                "throughput_per_min": r.throughput_per_min,
            })
        self.minute += 1
        return records

    def run(self) -> list[dict]:
        """Run a full day and return the flat list of per-ride-per-minute rows."""
        out: list[dict] = []
        while self.minute <= CLOSE_MINUTE:
            out.extend(self.step())
        return out