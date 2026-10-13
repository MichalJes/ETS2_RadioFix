# ETS2 / ATS RadioFix

Fresh `live_streams.sii` and `live_streams.json` files for the in-game radio players in [Euro Truck Simulator 2](https://eurotrucksimulator2.com/) and [American Truck Simulator](https://americantrucksimulator.com/).

[![CI](https://github.com/MichalJes/ETS2_RadioFix/actions/workflows/ci.yml/badge.svg)](https://github.com/MichalJes/ETS2_RadioFix/actions/workflows/ci.yml) [![Update radio stations](https://github.com/MichalJes/ETS2_RadioFix/actions/workflows/update-stations.yml/badge.svg)](https://github.com/MichalJes/ETS2_RadioFix/actions/workflows/update-stations.yml) [![Latest station data](https://img.shields.io/github/v/release/MichalJes/ETS2_RadioFix?filter=latest-data&label=latest%20data)](https://github.com/MichalJes/ETS2_RadioFix/releases/tag/latest-data) [![License: GPL v3](https://img.shields.io/github/license/MichalJes/ETS2_RadioFix)](LICENSE)

The station list is regenerated from the community [Truck Simulator Radio Stations wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations) and the public [Radio-Browser](https://www.radio-browser.info/) directory. Dead streams are filtered out before the generated files are committed.

## Quick download

| File | Use |
| --- | --- |
| [`live_streams.sii`](live_streams.sii) | Drop-in replacement for ETS2/ATS radio stations. |
| [`live_streams.json`](live_streams.json) | JSON station list for tools, comparisons, and downstream automation. |
| [`STATIONS.md`](STATIONS.md) | Generated per-station status report. |
| [`VALIDATION.md`](VALIDATION.md) | Generated dead-stream report. |
| [Latest station data release](https://github.com/MichalJes/ETS2_RadioFix/releases/tag/latest-data) | Most recently published release assets and checksums. |

## Installation

1. Open your ETS2 or ATS documents folder, for example:
   - `C:\Users\[USERNAME]\Documents\Euro Truck Simulator 2\`
   - `C:\Users\[USERNAME]\Documents\American Truck Simulator\`
2. Back up your existing `live_streams.sii`.
3. Download this repo's latest [`live_streams.sii`](live_streams.sii).
4. Replace the file in your game documents folder.
5. Start the game and open the in-game radio player.

The game reads `live_streams.sii` directly. `live_streams.json` is provided for tools, comparisons, and downstream automation.

## Current generated data

Latest committed validation:

- **Live stations:** 1210
- **Dead streams filtered out:** 187
- **Country/region sections:** 96
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

# Radio-Browser only (useful when Fandom is unavailable)
python scraper/main.py --no-fandom

# Permit a partial refresh if one enabled source fails
python scraper/main.py --allow-partial

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

Enabled sources must all succeed by default; a source failure exits before writing artifacts. Use `--no-fandom` to explicitly select Radio-Browser alone, or `--allow-partial` to accept data from the remaining source. Empty fetch results are rejected even with partial output enabled. Scheduled updates keep the strict default to avoid silently replacing the dataset with incomplete source coverage.

Stream validation connects directly to validated public IP addresses and retains normal HTTPS certificate and hostname verification. It does not use HTTP(S) proxy environment variables; proxy-only networks can scrape sources but cannot validate streams without direct connectivity.

## Automation and quality checks

This repo has three GitHub Actions workflow areas:

- **CI**: runs on pushes and pull requests; checks Python compilation, unit tests, scraper smoke output, and `live_streams.sii` / `live_streams.json` consistency.
- **Update radio stations**: runs on the 1st and 15th of each month and can also be triggered manually. It regenerates station data, opens an auto-update PR when files change, and auto-merges once checks pass. Because PRs created with `GITHUB_TOKEN` do not trigger ordinary PR workflows, the update job explicitly dispatches CI on the generated branch using `actions: write`.
- **Releases**: publishes versioned bundles and a mutable `latest-data` release containing generated station files plus checksums. The `latest-data` release is updated manually from the workflow when you want a release-asset snapshot of the current committed data.

Repository settings must permit Actions-created PRs and auto-merge, with the CI `test` check required by branch protection to enforce passing checks before merging.

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

## Contributing

- Station additions should ideally go upstream to the Fandom wiki or Radio-Browser first; this repo imports from both.
- Use the issue templates for dead stations, missing stations, and scraper/tooling bugs.
- Avoid hand-editing generated station files unless the scraper or source import cannot represent the change.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and PR expectations.

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
