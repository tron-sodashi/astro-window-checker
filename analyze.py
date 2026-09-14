"""
Turns the raw clearoutside.com forecast dict into, for each of the
next several days: whether a night (deep-sky) session and/or a day
(solar) session looks feasible, and the specific safe time range(s)
if so.

The core idea:
  1. Build one continuous hour-by-hour timeline across all fetched
     days (a dict of datetime -> that hour's data).
  2. For each day, work out the calendar-time window that matters:
       - "day session"   = sunrise -> sunset (same calendar date)
       - "night session" = astronomical dusk (that evening) ->
                            astronomical dawn (the *next* morning)
  3. Walk the timeline within that window hour by hour, mark each
     hour "safe" or not against the thresholds in config.py, and
     merge consecutive safe hours into windows.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import config


@dataclass
class SafeWindow:
    start: datetime
    end: datetime

    def __str__(self) -> str:
        same_day = self.start.date() == self.end.date()
        end_fmt = "%H:%M" if same_day else "%a %H:%M"
        return f"{self.start:%a %H:%M} \u2013 {self.end:{end_fmt}}"


@dataclass
class DayResult:
    day_date: date
    day_windows: list       # list[SafeWindow], solar/daytime
    night_windows: list     # list[SafeWindow], deep-sky
    night_data_incomplete: bool  # True if the night runs past the fetched range
    sunrise: str
    sunset: str
    astro_dusk: str
    astro_dawn: str
    moon_illumination: str
    moon_phase: str


def _parse_from_day(raw: dict) -> date:
    d = raw["gen-info"]["forecast"]["from-day"]  # "dd/MM/yy"
    return datetime.strptime(d, "%d/%m/%y").date()


def _combine(day_date: date, hhmm: str) -> datetime:
    h, m = hhmm.split(":")
    return datetime(day_date.year, day_date.month, day_date.day, int(h), int(m))


def _build_timeline(raw: dict, start_date: date) -> dict:
    """
    dict[datetime (top of hour)] -> hour's data dict

    clearoutside.com does NOT bucket its hourly detail table into plain
    midnight-to-midnight calendar days. Each "day-i" card is built
    around one night, so within that single card's hours dict:
      - hour labels 12-23 belong to that card's own date (evening)
      - hour labels 00-11 actually belong to the *following* date
        (that night's early morning, shown alongside the evening it
        followed)
    This was confirmed against a live clearoutside.com screenshot,
    where a card labelled "Wednesday" had its 00-11 hours actually
    equal to Thursday's forecast. Because the 7 fetched cards overlap
    like shingles (day-i's tail is day-(i+1)'s true morning), a given
    date's true 00-11 data is actually sourced from the *previous*
    card, and this loop naturally reassembles that correctly.
    """
    timeline = {}
    days = raw["forecast"]
    for i in range(len(days)):
        card_date = start_date + timedelta(days=i)
        hours = days[f"day-{i}"]["hours"]
        for hour_str, hour_data in hours.items():
            hour = int(hour_str)
            entry_date = card_date if hour >= 12 else card_date + timedelta(days=1)
            ts = datetime(entry_date.year, entry_date.month, entry_date.day, hour)
            timeline[ts] = hour_data
    return timeline


def _hour_is_safe(hour_data: dict, max_cloud: int) -> bool:
    try:
        total_clouds = float(hour_data["total-clouds"])
        precip_prob = float(hour_data["prec-probability"])
    except (KeyError, ValueError, TypeError):
        return False  # missing/bad data -> treat as not-safe, don't guess
    return total_clouds <= max_cloud and precip_prob <= config.MAX_PRECIP_PROB


def _safe_windows_in_range(
    timeline: dict, start: datetime, end: datetime, max_cloud: int
) -> tuple:
    """
    Walks hourly from `start` (rounded down to the hour) to `end`,
    merges consecutive safe hours, and returns
    (list[SafeWindow], data_incomplete: bool).
    `data_incomplete` is True if part of [start, end) falls outside
    the fetched timeline (e.g. the last night in a 7-day forecast).
    """
    cur = start.replace(minute=0, second=0, microsecond=0)
    windows = []
    run_start = None
    incomplete = False

    while cur < end:
        hour_data = timeline.get(cur)
        if hour_data is None:
            incomplete = True
            if run_start is not None:
                windows.append(SafeWindow(run_start, cur))
                run_start = None
            cur += timedelta(hours=1)
            continue

        if _hour_is_safe(hour_data, max_cloud):
            if run_start is None:
                run_start = cur
        else:
            if run_start is not None:
                windows.append(SafeWindow(run_start, cur))
                run_start = None
        cur += timedelta(hours=1)

    if run_start is not None:
        windows.append(SafeWindow(run_start, end))

    min_span = timedelta(hours=config.MIN_WINDOW_HOURS)
    windows = [w for w in windows if (w.end - w.start) >= min_span]
    return windows, incomplete


def analyze(raw: dict) -> list:
    """Returns a list[DayResult], one per fetched day, in order."""
    start_date = _parse_from_day(raw)
    timeline = _build_timeline(raw, start_date)
    days = raw["forecast"]
    num_days = min(len(days), config.DAYS_AHEAD)

    results = []
    for i in range(num_days):
        day_date = start_date + timedelta(days=i)
        day = days[f"day-{i}"]
        sun = day["sun"]
        moon = day["moon"]

        sunrise = _combine(day_date, sun["rise"])
        sunset = _combine(day_date, sun["set"])
        day_windows, _ = _safe_windows_in_range(
            timeline, sunrise, sunset, config.MAX_CLOUD_DAY
        )

        astro_dusk = _combine(day_date, sun["astro-dark"][0])
        astro_dawn = _combine(day_date + timedelta(days=1), sun["astro-dark"][1])
        night_windows, incomplete = _safe_windows_in_range(
            timeline, astro_dusk, astro_dawn, config.MAX_CLOUD_NIGHT
        )

        results.append(
            DayResult(
                day_date=day_date,
                day_windows=day_windows,
                night_windows=night_windows,
                night_data_incomplete=incomplete,
                sunrise=sun["rise"],
                sunset=sun["set"],
                astro_dusk=sun["astro-dark"][0],
                astro_dawn=sun["astro-dark"][1],
                moon_illumination=moon["phase"]["percentage"],
                moon_phase=moon["phase"]["name"],
            )
        )

    return results
