# ETS2_RadioFix

Regularly updated `live_streams.sii` and `live_streams.json` files for [Euro Truck Simulator 2](https://eurotrucksimulator2.com/) and [American Truck Simulator](https://americantrucksimulator.com/), sourced from the community [Radio Stations wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations) and the [Radio-Browser](https://www.radio-browser.info/) directory.

## Installation

1. Open your ETS2 or ATS documents folder, for example:
   - `C:\Users\[USERNAME]\Documents\Euro Truck Simulator 2\`
   - `C:\Users\[USERNAME]\Documents\American Truck Simulator\`
2. Back up your existing `live_streams.sii`.
3. Download this repo's latest `live_streams.sii`.
4. Replace the file in your game documents folder.

The game reads `live_streams.sii` directly. `live_streams.json` is provided for tools, comparisons, and downstream automation.

## Current generated data

Latest committed validation:

- **Live stations:** 1085
- **Dead streams filtered out:** 213
- **Country/region sections:** 90 plus `Unknown`
- **Generated status report:** [STATIONS.md](STATIONS.md)
- **Dead-stream report:** [VALIDATION.md](VALIDATION.md)

`STATIONS.md` is the source of truth for current per-station status. The summary above should be updated whenever the generated data is refreshed.

## Scraper

The `scraper/` folder contains a Python CLI that regenerates the project artifacts:

- fetches stations from the Fandom wiki via the MediaWiki API
- fetches additional stations from Radio-Browser, deduplicated by stream URL
- validates stream URLs and excludes dead streams by default
- writes `live_streams.sii`, `live_streams.json`, `STATIONS.md`, and `VALIDATION.md`

Requirements:

- Python 3.10+
- no third-party runtime dependencies

Usage:

```bash
# Full run: scrape, validate, and regenerate all default artifacts
python scraper/main.py

# Skip validation and write all scraped stations
python scraper/main.py --no-validate

# Write to custom output paths
python scraper/main.py \
  --output /tmp/live_streams.sii \
  --json /tmp/live_streams.json \
  --report /tmp/VALIDATION.md \
  --stations /tmp/STATIONS.md

# Single country/region only
python scraper/main.py --country "United Kingdom"

# Fandom wiki only, without Radio-Browser additions
python scraper/main.py --no-radiobrowser

# Pull more/fewer stations from Radio-Browser, default is 1000
python scraper/main.py --radiobrowser-limit 2000
```

## Automation and quality checks

This repo has two GitHub Actions workflows:

- **CI**: runs on pushes and pull requests; checks Python compilation, unit tests, scraper smoke output, and `live_streams.sii` / `live_streams.json` consistency.
- **Update radio stations**: runs on the 1st and 15th of each month and can also be triggered manually. It regenerates station data, opens an auto-update PR when files change, and auto-merges once checks pass.

Useful local checks:

```bash
python -m compileall -q .
python -m unittest discover -s tests
python tests/verify_artifacts.py
```

Optional development checks used by CI/audits:

```bash
uvx ruff check .
uvx bandit -q -r . -x ./.git
```

## Project status

Completed:

- [x] Scrape stations from the Fandom wiki automatically
- [x] Add Radio-Browser as a second station source
- [x] Validate stream URLs and filter dead streams
- [x] Generate `live_streams.sii`, `live_streams.json`, `STATIONS.md`, and `VALIDATION.md`
- [x] Scheduled auto-update workflow
- [x] Auto-open pull requests when generated station data changes
- [x] Keep `live_streams.json` in sync with generated `.sii` output
- [x] ISO 639-3 language code standardisation across generated stations
- [x] Pull request CI for compile, unit, smoke, and generated-artifact checks
- [x] Basic SSRF hardening for stream validation in CI

Open/ongoing:

- [ ] Continue improving station coverage and upstream source parsing
- [ ] Retire or replace legacy helper scripts if downstream users no longer need them
