"""How far a posting is from home, for the Fall section's radius filter.

Job locations are free text ("Orlando, FL", "US-FL-Titusville", "Cape Canaveral,
Florida; Hawthorne, CA"), so instead of a geocoding service this keeps a small
list of Florida places with their coordinates. A place not on the list means
"distance unknown", and the posting stays out of the radius section.
"""
from __future__ import annotations

import math
import re

# (name, lat, lon). Central Florida plus the Space Coast and nearby cities.
PLACES = [
    ("orlando", 28.5384, -81.3789), ("lake nona", 28.3784, -81.2472), ("oviedo", 28.6700, -81.2081),
    ("winter park", 28.6000, -81.3392), ("winter springs", 28.6989, -81.3081), ("sanford", 28.8003, -81.2731),
    ("lake mary", 28.7589, -81.3178), ("heathrow", 28.7631, -81.3687), ("longwood", 28.7031, -81.3384),
    ("altamonte springs", 28.6611, -81.3656), ("casselberry", 28.6778, -81.3279), ("maitland", 28.6278, -81.3631),
    ("apopka", 28.6934, -81.5322), ("ocoee", 28.5692, -81.5440), ("winter garden", 28.5653, -81.5862),
    ("windermere", 28.4956, -81.5348), ("kissimmee", 28.2920, -81.4076), ("st. cloud", 28.2489, -81.2812),
    ("saint cloud", 28.2489, -81.2812), ("celebration", 28.3253, -81.5331), ("lake buena vista", 28.3936, -81.5386),
    ("bay lake", 28.3881, -81.5651), ("clermont", 28.5494, -81.7729), ("davenport", 28.1614, -81.6017),
    ("haines city", 28.1142, -81.6179), ("lakeland", 28.0395, -81.9498), ("mount dora", 28.8025, -81.6445),
    ("tavares", 28.8042, -81.7256), ("eustis", 28.8528, -81.6853), ("leesburg", 28.8108, -81.8779),
    ("deltona", 28.9005, -81.2637), ("deland", 29.0283, -81.3031), ("daytona beach", 29.2108, -81.0228),
    ("ormond beach", 29.2858, -81.0559), ("port orange", 29.1383, -80.9956), ("new smyrna beach", 29.0258, -80.9270),
    ("edgewater", 28.9889, -80.9023), ("titusville", 28.6122, -80.8076), ("kennedy space center", 28.5729, -80.6490),
    ("merritt island", 28.3581, -80.6823), ("cape canaveral", 28.4058, -80.6048), ("cocoa beach", 28.3200, -80.6076),
    ("cocoa", 28.3861, -80.7420), ("rockledge", 28.3506, -80.7253), ("viera", 28.2470, -80.7290),
    ("patrick", 28.2346, -80.6100), ("satellite beach", 28.1761, -80.5901), ("west melbourne", 28.0717, -80.6534),
    ("melbourne", 28.0836, -80.6081), ("palm bay", 28.0345, -80.5887), ("sebastian", 27.8164, -80.4706),
    ("vero beach", 27.6386, -80.3973), ("tampa", 27.9506, -82.4572), ("plant city", 28.0186, -82.1146),
    ("ocala", 29.1872, -82.1401), ("gainesville", 29.6516, -82.3248), ("jacksonville", 30.3322, -81.6557),
]
# Names that only exist in Florida; every other name needs "FL"/"Florida" next to it
# (so Melbourne, Australia and Jacksonville, NC don't count).
UNIQUE = {"orlando", "lake nona", "oviedo", "winter springs", "altamonte springs", "apopka", "ocoee", "kissimmee",
          "lake buena vista", "daytona beach", "ormond beach", "port orange", "new smyrna beach",
          "kennedy space center", "merritt island", "cape canaveral", "cocoa beach", "satellite beach"}
FL_RX = re.compile(r"(?i)\bfl\b|florida|\bus-fl")
REMOTE_RX = re.compile(r"(?i)(?<![a-z])remote(?![a-z])")
_PLACE_RX = [(n, lat, lon, re.compile(r"(?i)(?<![a-z])" + re.escape(n) + r"(?![a-z])")) for n, lat, lon in PLACES]


def miles_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def nearest(location: str, home: tuple[float, float]) -> tuple[float, str] | None:
    """(miles, place) for the closest known place in a location string, or None."""
    best = None
    for part in re.split(r"[;|]| / ", location or ""):
        fl = bool(FL_RX.search(part))
        for name, lat, lon, rx in _PLACE_RX:
            if rx.search(part) and (fl or name in UNIQUE):
                d = miles_between(home, (lat, lon))
                if best is None or d < best[0]:
                    best = (d, name.title())
                break  # longest names come first where it matters ("cocoa beach" before "cocoa")
    return best


def is_remote(location: str) -> bool:
    return bool(REMOTE_RX.search(location or ""))
