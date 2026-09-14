"""
Exercises analyze.py against hand-built fake forecasts, so the date/hour
assignment and windowing/merging logic can be checked without hitting
clearoutside.com.

Run with: python3 test_analyze.py
"""

import config
import analyze


def hour(total_clouds, precip=0):
    return {"total-clouds": str(total_clouds), "prec-probability": str(precip)}


def make_card(evening_hours, morning_hours, rise, set_, astro_dusk, astro_dawn):
    """
    Mimics one real clearoutside.com "day card": hours 12-23 are this
    card's own evening, hours 00-11 (listed after) are the *following*
    date's morning -- matching the real site's structure.
    """
    hours_dict = {}
    for h in range(12, 24):
        hours_dict[f"{h:02d}"] = evening_hours[h]
    for h in range(0, 12):
        hours_dict[f"{h:02d}"] = morning_hours[h]
    return {
        "date": {"long": "x", "short": "x"},
        "sun": {
            "rise": rise, "set": set_, "transit": "12:00",
            "civil-dark": ["x", "x"], "nautical-dark": ["x", "x"],
            "astro-dark": [astro_dusk, astro_dawn],
        },
        "moon": {"rise": "x", "set": "x",
                  "phase": {"name": "Waxing Gibbous", "percentage": "40%"}},
        "hours": hours_dict,
    }


def flat(value, overrides=None):
    d = {h: hour(value) for h in range(24)}
    if overrides:
        for h, v in overrides.items():
            d[h] = hour(v)
    return d


def test_wednesday_regression():
    """
    Reproduces the exact bug reported against a live clearoutside.com
    screenshot: a real Wednesday with NO clear daytime hour anywhere
    (76-100% cloud all day) was incorrectly reported as having a clear
    07:00-08:00 window, because that data was actually Thursday's
    morning mislabelled as Wednesday's.
    """
    config.DAYS_AHEAD = 3

    # Tuesday's card: its own evening doesn't matter here; its "00-11"
    # tail is the REAL Wednesday morning -- uniformly cloudy, per the
    # screenshot.
    tuesday = make_card(
        evening_hours=flat(80),
        morning_hours=flat(85),  # -> real Wed 00:00-11:00
        rise="05:33", set_="17:52", astro_dusk="19:05", astro_dawn="04:19",
    )

    # Wednesday's card: its own evening (real Wed 12-23) is also
    # uniformly cloudy, matching the screenshot exactly (76-100%, no
    # window). Its "00-11" tail is the real THURSDAY morning, which we
    # deliberately make clear -- this is the data that was previously
    # mis-attributed to Wednesday.
    wednesday = make_card(
        evening_hours=flat(90, overrides={17: 76, 18: 57, 21: 77}),
        morning_hours=flat(5),  # -> real Thu 00:00-11:00, genuinely clear
        rise="05:34", set_="17:49", astro_dusk="19:02", astro_dawn="04:21",
    )

    # Thursday's card: needed so Thursday's own day-window can be
    # checked; contents don't matter much beyond being clear at day.
    thursday = make_card(
        evening_hours=flat(80),
        morning_hours=flat(80),
        rise="05:35", set_="17:48", astro_dusk="19:01", astro_dawn="04:23",
    )

    raw = {
        "gen-info": {"forecast": {"from-day": "15/09/26", "to-day": "21/09/26"}},
        "sky-quality": {},
        "forecast": {"day-0": tuesday, "day-1": wednesday, "day-2": thursday},
    }

    results = analyze.analyze(raw)
    tue, wed, thu = results

    # The bug: Wednesday must NOT show a false clear window.
    assert wed.day_windows == [], f"expected no Wed window, got {wed.day_windows}"

    # The data wasn't lost -- it correctly belongs to Thursday's
    # morning instead (hours 05:00-11:00, before Thursday's own
    # sunset makes it a "day" window; here it's clear from 05-11).
    assert len(thu.day_windows) == 1
    assert str(thu.day_windows[0]) == "Thu 05:00 \u2013 12:00"

    print("Wednesday regression test passed.")


def test_night_window_merges_across_midnight():
    config.DAYS_AHEAD = 2
    day0 = make_card(
        evening_hours=flat(80, overrides={20: 10, 21: 10, 22: 10, 23: 10}),
        morning_hours=flat(15, overrides={3: 90, 4: 90}),  # next day's 00-02 clear, 03-04 cloudy
        rise="05:45", set_="17:50", astro_dusk="19:15", astro_dawn="05:00",
    )
    day1 = make_card(
        evening_hours=flat(80), morning_hours=flat(80),
        rise="05:46", set_="17:49", astro_dusk="19:14", astro_dawn="05:01",
    )
    raw = {
        "gen-info": {"forecast": {"from-day": "14/09/26", "to-day": "20/09/26"}},
        "sky-quality": {},
        "forecast": {"day-0": day0, "day-1": day1},
    }
    results = analyze.analyze(raw)
    day0_result = results[0]
    assert [str(w) for w in day0_result.night_windows] == ["Mon 20:00 \u2013 Tue 03:00"], \
        day0_result.night_windows
    print("Midnight-crossing merge test passed.")


if __name__ == "__main__":
    test_wednesday_regression()
    test_night_window_merges_across_midnight()
