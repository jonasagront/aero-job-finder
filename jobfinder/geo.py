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


# ---------------------------------------------------------------- anywhere in the U.S.
# For the All opportunities tab's state and distance filters. Cities on the list give a
# distance to the city; anything else with a state gives the distance to the state's
# middle, marked approximate.

STATES = {
    "AL": ("alabama", 32.8, -86.8), "AK": ("alaska", 61.4, -152.3), "AZ": ("arizona", 34.2, -111.7),
    "AR": ("arkansas", 34.9, -92.4), "CA": ("california", 37.2, -119.5), "CO": ("colorado", 39.0, -105.5),
    "CT": ("connecticut", 41.6, -72.7), "DE": ("delaware", 39.0, -75.5), "FL": ("florida", 28.6, -82.4),
    "GA": ("georgia", 32.7, -83.4), "HI": ("hawaii", 20.8, -156.3), "ID": ("idaho", 44.4, -114.6),
    "IL": ("illinois", 40.0, -89.2), "IN": ("indiana", 39.9, -86.3), "IA": ("iowa", 42.1, -93.5),
    "KS": ("kansas", 38.5, -98.4), "KY": ("kentucky", 37.5, -85.3), "LA": ("louisiana", 31.1, -92.0),
    "ME": ("maine", 45.4, -69.2), "MD": ("maryland", 39.0, -76.8), "MA": ("massachusetts", 42.3, -71.8),
    "MI": ("michigan", 44.3, -85.4), "MN": ("minnesota", 46.3, -94.3), "MS": ("mississippi", 32.7, -89.7),
    "MO": ("missouri", 38.4, -92.5), "MT": ("montana", 47.0, -109.6), "NE": ("nebraska", 41.5, -99.8),
    "NV": ("nevada", 39.3, -116.6), "NH": ("new hampshire", 43.7, -71.6), "NJ": ("new jersey", 40.2, -74.7),
    "NM": ("new mexico", 34.4, -106.1), "NY": ("new york", 42.9, -75.5), "NC": ("north carolina", 35.6, -79.4),
    "ND": ("north dakota", 47.5, -100.5), "OH": ("ohio", 40.3, -82.8), "OK": ("oklahoma", 35.6, -97.5),
    "OR": ("oregon", 43.9, -120.6), "PA": ("pennsylvania", 40.9, -77.8), "RI": ("rhode island", 41.7, -71.5),
    "SC": ("south carolina", 33.9, -80.9), "SD": ("south dakota", 44.4, -100.2), "TN": ("tennessee", 35.9, -86.4),
    "TX": ("texas", 31.5, -99.3), "UT": ("utah", 39.3, -111.7), "VT": ("vermont", 44.1, -72.7),
    "VA": ("virginia", 37.5, -78.9), "WA": ("washington", 47.4, -120.5), "WV": ("west virginia", 38.6, -80.6),
    "WI": ("wisconsin", 44.6, -89.9), "WY": ("wyoming", 43.0, -107.5), "DC": ("district of columbia", 38.9, -77.0),
    "PR": ("puerto rico", 18.2, -66.5),
}
# (city, state, lat, lon): big metros plus the aerospace, defense and motorsport towns postings name
CITIES = [
    ("huntsville", "AL", 34.73, -86.59), ("mobile", "AL", 30.69, -88.04), ("birmingham", "AL", 33.52, -86.80),
    ("phoenix", "AZ", 33.45, -112.07), ("tucson", "AZ", 32.22, -110.97), ("chandler", "AZ", 33.31, -111.84),
    ("mesa", "AZ", 33.42, -111.83), ("tempe", "AZ", 33.43, -111.94), ("scottsdale", "AZ", 33.49, -111.93),
    ("los angeles", "CA", 34.05, -118.24), ("long beach", "CA", 33.77, -118.19), ("el segundo", "CA", 33.92, -118.42),
    ("hawthorne", "CA", 33.92, -118.35), ("torrance", "CA", 33.84, -118.34), ("irvine", "CA", 33.68, -117.83),
    ("costa mesa", "CA", 33.64, -117.92), ("huntington beach", "CA", 33.66, -118.00), ("san diego", "CA", 32.72, -117.16),
    ("palmdale", "CA", 34.58, -118.12), ("lancaster", "CA", 34.70, -118.14), ("mojave", "CA", 35.05, -118.17),
    ("san francisco", "CA", 37.77, -122.42), ("san jose", "CA", 37.34, -121.89), ("sunnyvale", "CA", 37.37, -122.04),
    ("mountain view", "CA", 37.39, -122.08), ("palo alto", "CA", 37.44, -122.14), ("santa clara", "CA", 37.35, -121.96),
    ("fremont", "CA", 37.55, -121.99), ("oakland", "CA", 37.80, -122.27), ("sacramento", "CA", 38.58, -121.49),
    ("pasadena", "CA", 34.15, -118.14), ("burbank", "CA", 34.18, -118.31), ("santa barbara", "CA", 34.42, -119.70),
    ("long beach", "CA", 33.77, -118.19), ("vandenberg", "CA", 34.74, -120.57), ("livermore", "CA", 37.68, -121.77),
    ("denver", "CO", 39.74, -104.99), ("colorado springs", "CO", 38.83, -104.82), ("boulder", "CO", 40.01, -105.27),
    ("littleton", "CO", 39.61, -105.02), ("louisville", "CO", 39.98, -105.13), ("aurora", "CO", 39.73, -104.83),
    ("englewood", "CO", 39.65, -104.99), ("golden", "CO", 39.76, -105.22), ("broomfield", "CO", 39.92, -105.09),
    ("hartford", "CT", 41.76, -72.69), ("east hartford", "CT", 41.78, -72.61), ("stratford", "CT", 41.18, -73.13),
    ("groton", "CT", 41.35, -72.08), ("windsor locks", "CT", 41.93, -72.63), ("wilmington", "DE", 39.74, -75.55),
    ("washington", "DC", 38.90, -77.04),
    ("miami", "FL", 25.76, -80.19), ("jupiter", "FL", 26.93, -80.09), ("west palm beach", "FL", 26.72, -80.05),
    ("fort lauderdale", "FL", 26.12, -80.14), ("pensacola", "FL", 30.42, -87.22), ("fort walton beach", "FL", 30.42, -86.62),
    ("niceville", "FL", 30.52, -86.48), ("tallahassee", "FL", 30.44, -84.28), ("clearwater", "FL", 27.97, -82.80),
    ("st. petersburg", "FL", 27.77, -82.64), ("sarasota", "FL", 27.34, -82.53), ("fort myers", "FL", 26.64, -81.87),
    ("atlanta", "GA", 33.75, -84.39), ("savannah", "GA", 32.08, -81.09), ("marietta", "GA", 33.95, -84.55),
    ("warner robins", "GA", 32.62, -83.63), ("columbus", "GA", 32.46, -84.99), ("honolulu", "HI", 21.31, -157.86),
    ("idaho falls", "ID", 43.49, -112.03), ("boise", "ID", 43.62, -116.20),
    ("chicago", "IL", 41.88, -87.63), ("peoria", "IL", 40.69, -89.59), ("rockford", "IL", 42.27, -89.09),
    ("indianapolis", "IN", 39.77, -86.16), ("speedway", "IN", 39.80, -86.25), ("fort wayne", "IN", 41.08, -85.14),
    ("cedar rapids", "IA", 41.98, -91.67), ("wichita", "KS", 37.69, -97.34), ("louisville", "KY", 38.25, -85.76),
    ("new orleans", "LA", 29.95, -90.07), ("boston", "MA", 42.36, -71.06), ("cambridge", "MA", 42.37, -71.11),
    ("lexington", "MA", 42.45, -71.23), ("bedford", "MA", 42.49, -71.28), ("waltham", "MA", 42.38, -71.24),
    ("andover", "MA", 42.66, -71.14), ("burlington", "MA", 42.50, -71.20), ("woburn", "MA", 42.48, -71.15),
    ("baltimore", "MD", 39.29, -76.61), ("columbia", "MD", 39.20, -76.86), ("laurel", "MD", 39.10, -76.85),
    ("greenbelt", "MD", 39.00, -76.88), ("annapolis junction", "MD", 39.12, -76.78), ("lexington park", "MD", 38.27, -76.45),
    ("detroit", "MI", 42.33, -83.05), ("ann arbor", "MI", 42.28, -83.74), ("warren", "MI", 42.51, -83.03),
    ("auburn hills", "MI", 42.69, -83.23), ("dearborn", "MI", 42.32, -83.18), ("grand rapids", "MI", 42.96, -85.66),
    ("minneapolis", "MN", 44.98, -93.27), ("st. paul", "MN", 44.95, -93.09), ("st. louis", "MO", 38.63, -90.20),
    ("kansas city", "MO", 39.10, -94.58), ("omaha", "NE", 41.26, -95.93), ("las vegas", "NV", 36.17, -115.14),
    ("reno", "NV", 39.53, -119.81), ("nashua", "NH", 42.77, -71.47), ("merrimack", "NH", 42.87, -71.49),
    ("albuquerque", "NM", 35.08, -106.65), ("los alamos", "NM", 35.89, -106.30), ("las cruces", "NM", 32.32, -106.76),
    ("new york", "NY", 40.71, -74.01), ("buffalo", "NY", 42.89, -78.88), ("rochester", "NY", 43.16, -77.61),
    ("syracuse", "NY", 43.05, -76.15), ("east aurora", "NY", 42.77, -78.61), ("long island", "NY", 40.79, -73.13),
    ("charlotte", "NC", 35.23, -80.84), ("mooresville", "NC", 35.58, -80.81), ("concord", "NC", 35.41, -80.58),
    ("huntersville", "NC", 35.41, -80.84), ("welcome", "NC", 35.90, -80.26), ("raleigh", "NC", 35.78, -78.64),
    ("durham", "NC", 35.99, -78.90), ("greensboro", "NC", 36.07, -79.79), ("statesville", "NC", 35.78, -80.89),
    ("cleveland", "OH", 41.50, -81.69), ("columbus", "OH", 39.96, -83.00), ("cincinnati", "OH", 39.10, -84.51),
    ("dayton", "OH", 39.76, -84.19), ("evendale", "OH", 39.25, -84.42), ("sandusky", "OH", 41.45, -82.71),
    ("oklahoma city", "OK", 35.47, -97.52), ("tulsa", "OK", 36.15, -95.99), ("portland", "OR", 45.52, -122.68),
    ("pittsburgh", "PA", 40.44, -80.00), ("philadelphia", "PA", 39.95, -75.17), ("king of prussia", "PA", 40.09, -75.40),
    ("state college", "PA", 40.79, -77.86), ("providence", "RI", 41.82, -71.41), ("charleston", "SC", 32.78, -79.93),
    ("greenville", "SC", 34.85, -82.40), ("north charleston", "SC", 32.85, -80.00), ("rapid city", "SD", 44.08, -103.23),
    ("tullahoma", "TN", 35.36, -86.21), ("arnold air force base", "TN", 35.39, -86.09), ("nashville", "TN", 36.16, -86.78),
    ("knoxville", "TN", 35.96, -83.92), ("oak ridge", "TN", 36.01, -84.27), ("memphis", "TN", 35.15, -90.05),
    ("houston", "TX", 29.76, -95.37), ("webster", "TX", 29.54, -95.12), ("dallas", "TX", 32.78, -96.80),
    ("fort worth", "TX", 32.76, -97.33), ("austin", "TX", 30.27, -97.74), ("san antonio", "TX", 29.42, -98.49),
    ("mcgregor", "TX", 31.44, -97.41), ("plano", "TX", 33.02, -96.70), ("grand prairie", "TX", 32.75, -97.00),
    ("el paso", "TX", 31.76, -106.49), ("brownsville", "TX", 25.90, -97.50), ("starbase", "TX", 25.99, -97.18),
    ("salt lake city", "UT", 40.76, -111.89), ("ogden", "UT", 41.22, -111.97), ("clearfield", "UT", 41.11, -112.03),
    ("promontory", "UT", 41.61, -112.55), ("arlington", "VA", 38.88, -77.10), ("reston", "VA", 38.96, -77.36),
    ("herndon", "VA", 38.97, -77.39), ("chantilly", "VA", 38.89, -77.43), ("dulles", "VA", 38.96, -77.45),
    ("mclean", "VA", 38.93, -77.18), ("falls church", "VA", 38.88, -77.17), ("alexandria", "VA", 38.80, -77.05),
    ("springfield", "VA", 38.79, -77.19), ("norfolk", "VA", 36.85, -76.29), ("newport news", "VA", 37.09, -76.47),
    ("hampton", "VA", 37.03, -76.35), ("dahlgren", "VA", 38.33, -77.04), ("wallops island", "VA", 37.94, -75.47),
    ("seattle", "WA", 47.61, -122.33), ("everett", "WA", 47.98, -122.20), ("renton", "WA", 47.48, -122.21),
    ("kent", "WA", 47.38, -122.23), ("redmond", "WA", 47.67, -122.12), ("bothell", "WA", 47.76, -122.21),
    ("auburn", "WA", 47.31, -122.23), ("tukwila", "WA", 47.47, -122.26), ("milwaukee", "WI", 43.04, -87.91),
    ("oshkosh", "WI", 44.02, -88.54), ("madison", "WI", 43.07, -89.40), ("cheyenne", "WY", 41.14, -104.82),
]
# "Orlando, FL", "US-FL-Titusville", "Denver (CO)": a capitalized code after a comma, dash or "US-"
_STATE_ABBR_RX = re.compile(r"(?:,|\s-|^|\bUS-|\bUSA-|\()\s*(" + "|".join(STATES) + r")(?=\b(?![a-z']))")
_STATE_NAME_RX = [(abbr, re.compile(rf"(?i)(?<![a-z]){'(?<!west )' if abbr == 'VA' else ''}{re.escape(name)}(?![a-z])"))
                  for abbr, (name, _, _) in STATES.items()]
_CITY_RX = [(c, st, lat, lon, re.compile(rf"(?i)(?<![a-z]){re.escape(c)}(?![a-z])")) for c, st, lat, lon in CITIES]


def us_places(location: str) -> list[dict]:
    """Each U.S. place a location string names: {"state", "city", "lat", "lon", "approx"}.
    A part with only a state counts at the state's middle (approx = True)."""
    out = []
    for part in re.split(r"[;|]| / |\n", location or ""):
        part = part.strip()
        if not part:
            continue
        states = [m.group(1) for m in _STATE_ABBR_RX.finditer(part)]
        states += [abbr for abbr, rx in _STATE_NAME_RX if rx.search(part)]
        # "Washington, DC" and "New York, NY" name a city like a state; the abbreviation wins
        city = None
        for c, st, lat, lon, rx in _CITY_RX:
            if rx.search(part) and (st in states or (not states and c in _UNIQUE_CITIES)):
                city = (c, st, lat, lon)
                break
        if city:
            out.append({"state": city[1], "city": city[0].title(), "lat": city[2], "lon": city[3], "approx": False})
            continue
        # Florida places the Fall section already knows
        fl = nearest(part, (28.6024, -81.2001))
        if fl:
            for name, lat, lon, _ in _PLACE_RX:
                if name.title() == fl[1]:
                    out.append({"state": "FL", "city": fl[1], "lat": lat, "lon": lon, "approx": False})
                    break
            continue
        if states:
            st = states[0]
            out.append({"state": st, "city": "", "lat": STATES[st][1], "lon": STATES[st][2], "approx": True})
    return out


# City names that point to one place even without a state
_UNIQUE_CITIES = {"huntsville", "el segundo", "hawthorne", "mojave", "palmdale", "colorado springs", "boulder",
                  "albuquerque", "los alamos", "tullahoma", "starbase", "mooresville", "wichita", "houston",
                  "seattle", "denver", "phoenix", "tucson", "pittsburgh", "chicago", "boston", "detroit",
                  "san diego", "los angeles", "san francisco", "dallas", "austin", "san antonio", "atlanta",
                  "huntington beach", "long beach", "chantilly", "herndon", "reston", "dahlgren", "idaho falls"}


def place_info(location: str, home: tuple[float, float] | None) -> dict:
    """For the page's filters: U.S. states named, miles from home to the nearest place
    (None if no place is known), whether that distance is approximate, and remote."""
    places = us_places(location)
    info: dict = {"states": sorted({p["state"] for p in places}), "remote": is_remote(location)}
    if home and places:
        best = min(places, key=lambda p: miles_between(home, (p["lat"], p["lon"])))
        info["mi"] = round(miles_between(home, (best["lat"], best["lon"])))
        if best["approx"]:
            info["approx"] = True
    return info
