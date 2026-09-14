"""
Renders a list[DayResult] into a single self-contained HTML page.
No JS frameworks, no build step -- just a template string, so it can
be written straight into docs/index.html for GitHub Pages.
"""

from datetime import datetime, timezone

import config

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Astronomy window forecast</title>
<style>
  :root {{
    --bg: #0b0f1a;
    --card: #131a2b;
    --text: #e6e9f0;
    --muted: #8a93a6;
    --good: #35c46a;
    --bad: #3a4256;
    --accent: #6ea8fe;
  }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 780px;
    margin: 0 auto;
    padding: 24px 16px 60px;
    line-height: 1.5;
  }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  .subtitle {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 28px; }}
  .day-card {{
    background: var(--card);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
  }}
  .day-title {{ font-size: 1.05rem; font-weight: 600; margin-bottom: 6px; }}
  .day-meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 12px; }}
  .session {{ margin-top: 10px; }}
  .session-label {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
  .window {{
    display: inline-block;
    background: rgba(53, 196, 106, 0.15);
    border: 1px solid var(--good);
    color: var(--good);
    border-radius: 8px;
    padding: 4px 10px;
    margin: 4px 6px 0 0;
    font-size: 0.9rem;
  }}
  .none {{ color: var(--muted); font-size: 0.9rem; margin-top: 4px; }}
  .note {{ color: var(--accent); font-size: 0.8rem; margin-top: 4px; }}
  footer {{ color: var(--muted); font-size: 0.8rem; margin-top: 32px; }}
</style>
</head>
<body>
  <h1>Astronomy window forecast</h1>
  <div class="subtitle">
    Location: {lat}, {lon} &middot; Updated {updated}<br>
    Night window needs total cloud cover \u2264 {max_cloud_night}% &middot;
    Day window needs \u2264 {max_cloud_day}% &middot; precipitation chance \u2264 {max_precip}%
  </div>
  {day_cards}
  <footer>
    Data from <a href="https://clearoutside.com" style="color: var(--accent)">clearoutside.com</a>.
    This page is regenerated automatically and thresholds are configurable in
    <code>config.py</code>.
  </footer>
</body>
</html>
"""

_DAY_CARD_TEMPLATE = """
  <div class="day-card">
    <div class="day-title">{weekday}, {date_str}</div>
    <div class="day-meta">
      Sun {sunrise}\u2013{sunset} &middot; Astro dark {astro_dusk}\u2013{astro_dawn} &middot;
      Moon {moon_phase} ({moon_pct} illuminated)
    </div>
    <div class="session">
      <div class="session-label">Night (deep-sky)</div>
      {night_html}
    </div>
    <div class="session">
      <div class="session-label">Day (solar)</div>
      {day_html}
    </div>
  </div>
"""


def _windows_html(windows, incomplete_note=None) -> str:
    if not windows:
        html = '<div class="none">No safe window.</div>'
    else:
        html = "".join(f'<span class="window">{w}</span>' for w in windows)
    if incomplete_note:
        html += f'<div class="note">{incomplete_note}</div>'
    return html


def render(results: list) -> str:
    day_cards = []
    for r in results:
        night_note = (
            "Forecast data ends before this night's astro-dawn \u2014 "
            "the window may extend further than shown."
            if r.night_data_incomplete
            else None
        )
        day_cards.append(
            _DAY_CARD_TEMPLATE.format(
                weekday=r.day_date.strftime("%A"),
                date_str=r.day_date.strftime("%d %b %Y"),
                sunrise=r.sunrise,
                sunset=r.sunset,
                astro_dusk=r.astro_dusk,
                astro_dawn=r.astro_dawn,
                moon_phase=r.moon_phase,
                moon_pct=r.moon_illumination,
                night_html=_windows_html(r.night_windows, night_note),
                day_html=_windows_html(r.day_windows),
            )
        )

    return _PAGE_TEMPLATE.format(
        lat=config.LATITUDE,
        lon=config.LONGITUDE,
        updated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        max_cloud_night=config.MAX_CLOUD_NIGHT,
        max_cloud_day=config.MAX_CLOUD_DAY,
        max_precip=config.MAX_PRECIP_PROB,
        day_cards="".join(day_cards),
    )
