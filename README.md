> This project is maintained with the assistance of [Claude](https://claude.ai) (Anthropic).

# ETS2_RadioFix

A regularly updated `live_streams.sii` file for [Euro Truck Simulator 2](https://eurotrucksimulator2.com/) and [American Truck Simulator](https://americantrucksimulator.com/), sourced from the community [Radio Stations wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations) and the [Radio-Browser](https://www.radio-browser.info/) directory.

## Installation

1. Navigate to your ETS2/ATS documents folder — e.g. `C:\Users\[USERNAME]\Documents\Euro Truck Simulator 2\`
2. Back up your current `live_streams.sii` (rename or copy it elsewhere)
3. Replace it with the `live_streams.sii` from this repo

## Scraper

The `scraper/` folder contains a Python CLI that regenerates `live_streams.sii` automatically:

- Fetches all stations from the Fandom wiki via the MediaWiki API
- Fetches additional stations from the [Radio-Browser](https://www.radio-browser.info/) API (deduplicated against the Fandom set by stream URL)
- Validates every stream URL (dead streams are excluded)
- Outputs a fresh `live_streams.sii` and a `VALIDATION.md` report

**Requirements:** Python 3.9+, no third-party dependencies

**Usage:**
```bash
# Full run (scrape + validate, ~1-2 min)
python scraper/main.py

# Skip validation
python scraper/main.py --no-validate

# Single country only
python scraper/main.py --country "United Kingdom"

# Skip the Radio-Browser source (Fandom wiki only)
python scraper/main.py --no-radiobrowser

# Pull more/fewer stations from Radio-Browser (default: 1000)
python scraper/main.py --radiobrowser-limit 2000
```

**Last run:** 1098 live stations across 80 countries (1302 scraped, 204 dead filtered out)

See [STATIONS.md](STATIONS.md) for the full per-station live/dead status.

## Current status

### Countries covered
* [x] Azerbaijan
* [x] Belgium
* [x] Canada
* [x] Chile
* [x] Croatia
* [x] Czechia
* [x] Denmark
* [x] France
* [x] Iceland
* [x] Latvia
* [x] New Zealand
* [x] North Macedonia
* [x] Philippines
* [x] Portugal
* [x] Spain
* [x] Switzerland
* [x] Türkiye
* [x] United Kingdom
* [x] United States
* [x] Austria
* [x] Bulgaria
* [ ] Estonia
* [x] Finland
* [x] Germany
* [x] Hungary
* [x] Italy
* [ ] Lithuania
* [ ] Luxembourg
* [x] Netherlands
* [x] Norway
* [x] Poland
* [x] Romania
* [x] Russia
* [x] Serbia
* [x] Slovakia
* [x] Sweden
* [x] Ukraine

### Planned features
* [x] Scrape stations from Fandom wiki automatically
* [x] Add a second station source (Radio-Browser API)
* [x] Validate stream URLs and filter dead streams
* [x] Generate `VALIDATION.md` dead-stream report
* [ ] Scheduled auto-run to keep `live_streams.sii` up to date
* [ ] Auto-open pull request when new stations are found
* [ ] Add missing countries from the wiki
* [x] ISO 639-3 language code standardisation across all stations
