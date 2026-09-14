# Astronomy window forecast

Checks clearoutside.com's 7-day forecast for a fixed location and works out,
for each of the next few days, whether there's a safe window for a **night**
(deep-sky) session and/or a **day** (solar) session -- and if so, the exact
time range.

A live example of the output page is what ends up at `docs/index.html`
once it's run (see "Hosting it" below).

## How "safe" is decided

For each hour, clearoutside.com gives total cloud cover (%) and chance of
precipitation (%). An hour counts as usable if:

- **Night window**: total cloud cover ≤ `MAX_CLOUD_NIGHT` (default 30%)
- **Day window**: total cloud cover ≤ `MAX_CLOUD_DAY` (default 20%, stricter
  since solar observing needs a cleaner line to the Sun)
- Either way, chance of precipitation ≤ `MAX_PRECIP_PROB` (default 20%)

The **night** window is bounded by astronomical dusk/dawn (true darkness,
not just sunset/sunrise) for that date, which correctly spans midnight into
the next calendar day. The **day** window is bounded by sunrise/sunset.
Consecutive safe hours are merged into a single reported range, e.g.
`Mon 20:00 – Tue 03:00`.

Moon phase/illumination is shown for context but doesn't gate the window --
a bright moon makes a night less ideal for faint deep-sky targets, but
doesn't make it "unsafe," so it's left as a judgment call for you.

All thresholds live in `config.py` -- change them and re-run.

## Files

| File | What it does |
|---|---|
| `config.py` | Location (lat/long) and the thresholds above |
| `fetch.py` | Pulls the raw forecast (see "About the data source" below) |
| `analyze.py` | Turns raw hourly data into safe windows |
| `report.py` | Renders the results into `docs/index.html` |
| `main.py` | Runs the three steps above in order |
| `test_analyze.py` | Checks the windowing logic against synthetic data, no network needed |
| `.github/workflows/update.yml` | Runs `main.py` daily and commits the updated page |

## About the data source

Scraping is done by [`clear-outside-apy`](https://github.com/TheElevatedOne/ClearOutsideAPY),
a small, unofficial, open-source library that parses clearoutside.com's
HTML. It's not maintained by clearoutside.com itself, so if that site ever
changes its page layout, this library (specifically the single file at its
GitHub repo) is what would need a fix -- `analyze.py` and everything else
here doesn't touch HTML at all, it only consumes the clean dict that
library returns.

I couldn't test the live scrape from where I built this (no network access
to clearoutside.com), so **run `python main.py` once yourself and check the
output looks sane** before relying on it -- ideally cross-check a day or
two against clearoutside.com itself, the way the first real bug in this
project got caught.

One such bug already found and fixed: clearoutside.com's day cards aren't
plain calendar days -- each card bundles one whole night together with its
surrounding day, so hours 00-11 shown under e.g. "Wednesday" are actually
Thursday's early morning. `test_analyze.py`'s `test_wednesday_regression`
reproduces this exact scenario (a real screenshot showed a day with no
clear hour anywhere being reported as having one) and checks it's handled
correctly now. Worth keeping an eye out for other mismatches like this
during your own local run, since I can't verify against the live site
myself.

## Setup

1. **Set your location.** Edit `LATITUDE`/`LONGITUDE` in `config.py`. The
   placeholder values are approximate for Jatani, Odisha -- replace them
   with your actual observing site's coordinates for best accuracy.

2. **Try it locally:**
   ```
   pip install -r requirements.txt
   python main.py
   ```
   Open `docs/index.html` in a browser and sanity-check it against what
   clearoutside.com itself shows for your coordinates.

3. **Run the tests** (no network needed):
   ```
   python test_analyze.py
   ```

## Hosting it (GitHub Actions + GitHub Pages, free)

1. Create a new **public** GitHub repo and push this folder to it.
2. In the repo, go to **Settings → Pages**, and under "Build and
   deployment" set **Source: Deploy from a branch**, branch **main**,
   folder **/docs**. Save.
3. Go to the **Actions** tab, open "Update astronomy forecast", and click
   **Run workflow** once to generate the first real report (it also runs
   automatically every day at 01:00 UTC -- edit the `cron` line in
   `.github/workflows/update.yml` if you want a different time).
4. Your page will be live at `https://<your-username>.github.io/<repo-name>/`
   within a minute or two of the workflow finishing. Bookmark it.

No server to maintain, no cost, and it keeps itself up to date.

## If you'd rather get a notification instead of/as well as a webpage

The core pipeline (`fetch.py` + `analyze.py`) doesn't care how the result is
delivered -- `main.py` is the only place that currently writes to
`docs/index.html`. Sending an email or a Telegram/Discord message when a
good window shows up is a small addition to `main.py` (e.g. a webhook POST
or `smtplib` call) rather than a rewrite; happy to add that if you want it
later.
