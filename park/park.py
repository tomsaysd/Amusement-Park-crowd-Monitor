"""
The static description of the park: its zones, the rides in each zone, where
they sit on the map, and how far apart they are, with coordinates on a 0-100 grid.
"""

from dataclasses import dataclass, field
from math import hypot


@dataclass(frozen=True)
class Ride:
    ride_id: str
    name: str
    zone_id: str
    x: float
    y: float
    throughput_per_min: int     # How many guests the ride can load per simulated minute (its throughput).
    duration_min: int     # How long the ride takes in minutes.
    popularity: float       # Relative drawing power


@dataclass(frozen=True)
class Zone:
    zone_id: str
    name: str
    x: float
    y: float

# --------PARK LAYOUT (STATIC)-----
ZONES = [
    Zone("plaza",   "Entrance Plaza", 50, 12),
    Zone("frontier","Frontier Land",  18, 45),
    Zone("fantasy", "Fantasy Grove",  50, 55),
    Zone("future",  "Future World",   82, 45),
    Zone("splash",  "Splash Cove",    30, 82),
    Zone("kiddie",  "Kiddie Corner",  72, 82),
]

RIDES = [
    Ride("carousel",  "Grand Carousel",     "plaza",    50, 20, throughput_per_min=30, duration_min=3, popularity=0.30),
    Ride("minetrain", "Runaway Mine Train", "frontier", 14, 40, throughput_per_min=20, duration_min=3, popularity=0.90),
    Ride("logflume",  "Timber Log Flume",   "frontier", 24, 52, throughput_per_min=15, duration_min=6, popularity=0.60),
    Ride("boats",     "Enchanted Boats",    "fantasy",  44, 50, throughput_per_min=18, duration_min=6, popularity=0.40),
    Ride("manor",     "Haunted Manor",      "fantasy",  58, 60, throughput_per_min=16, duration_min=5, popularity=0.65),
    Ride("galaxy",    "Galaxy Coaster",     "future",   86, 40, throughput_per_min=22, duration_min=3, popularity=1.00),
    Ride("spinner",   "Space Spinner",      "future",   78, 52, throughput_per_min=20, duration_min=2, popularity=0.50),
    Ride("rapids",    "Thunder Rapids",     "splash",   30, 80, throughput_per_min=14, duration_min=8, popularity=0.70),
    Ride("teacups",   "Spinning Tea Cups",  "kiddie",   68, 78, throughput_per_min=24, duration_min=3, popularity=0.30),
    Ride("minicars",  "Junior Speedway",    "kiddie",   76, 86, throughput_per_min=20, duration_min=4, popularity=0.25),
]

ZONE_BY_ID = {z.zone_id: z for z in ZONES}
RIDE_BY_ID = {r.ride_id: r for r in RIDES}
RIDES_IN_ZONE = {z.zone_id: [r for r in RIDES if r.zone_id == z.zone_id] for z in ZONES}


def walk_minutes(from_ride: Ride, to_ride: Ride, walk_speed: float = 8.0) -> float:
    """Travel time in minutes between two rides at a fixed walking speed
    (grid-units per minute). Straight-line distance is fine for a POC; this is
    what introduces *spatial* realism -- guests take time to move, and they
    tend to hop to nearby rides, so neighbouring zones heat up together."""
    dist = hypot(from_ride.x - to_ride.x, from_ride.y - to_ride.y)
    return max(1.0, dist / walk_speed)