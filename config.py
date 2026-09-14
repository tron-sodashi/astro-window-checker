"""
All the knobs you're likely to want to turn live here.
"""

# --- Location -----------------------------------------------------------
# clearoutside.com wants lat/long as strings with 2 decimal places.
# These are approximate coordinates for Jatani, Odisha, India.
# Replace with the exact coordinates of your actual observing site
# (e.g. your backyard/roof) for the most accurate forecast -- cloud
# cover can vary meaningfully over even a few km.
LATITUDE = "20.16"
LONGITUDE = "85.71"

# --- "Is it safe" thresholds ---------------------------------------------
# An hour counts as usable for NIGHT (deep-sky) observing if total cloud
# cover is at or below this percentage.
MAX_CLOUD_NIGHT = 30

# Daytime (solar) observing needs a cleaner line to the Sun, so this is
# stricter by default.
MAX_CLOUD_DAY = 20

# An hour is excluded if the chance of precipitation is above this,
# regardless of cloud cover.
MAX_PRECIP_PROB = 20

# Ignore safe windows shorter than this many hours (set to 1 to keep
# every window, however short).
MIN_WINDOW_HOURS = 1

# How many upcoming days to report on (clearoutside gives at most 7).
DAYS_AHEAD = 7
