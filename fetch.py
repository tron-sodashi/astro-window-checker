"""
Pulls the raw 7-day forecast dict from clearoutside.com.

This uses the third-party open-source library `clear-outside-apy`
(https://github.com/TheElevatedOne/ClearOutsideAPY), which does the
actual HTML scraping/parsing of clearoutside.com. It's a small,
single-file, unofficial library -- if clearoutside.com ever changes
its page layout and this starts throwing errors, that library (or a
vendored copy of it) is the thing that needs a patch, not the analysis
code in analyze.py.
"""

from clear_outside_apy import ClearOutsideAPY

import config


def fetch_forecast() -> dict:
    """
    Returns the raw forecast dict, e.g.:

    {
      "gen-info": {"forecast": {"from-day": "19/02/25", ...}, ...},
      "sky-quality": {...},
      "forecast": {
        "day-0": {"date": {...}, "sun": {...}, "moon": {...}, "hours": {...}},
        ...
      }
    }

    Note: clearoutside.com's day cards are noon-anchored, not plain
    calendar days -- within a single "day-i" card, hour labels 00-11
    actually belong to the *following* calendar date (that night's
    early morning, shown alongside the evening it followed). This
    holds regardless of the `view` value below, which only changes
    display order. analyze.py's _build_timeline() is what correctly
    reassembles absolute dates from this; see the comment there.
    """
    api = ClearOutsideAPY(config.LATITUDE, config.LONGITUDE, view="midnight")
    api.update()
    return api.pull()
