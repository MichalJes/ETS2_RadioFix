# Contributing

Thanks for helping keep ETS2/ATS radio streams usable.

## Station data

The generated station files are built from:

- the community [Truck Simulator Radio Stations wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations)
- the public [Radio-Browser](https://www.radio-browser.info/) directory

For ordinary station additions or metadata fixes, prefer updating one of those upstream sources first. The scheduled scraper should pick up upstream changes during the next refresh.

Open an issue here when:

- a station is missing from both upstream sources
- a listed stream is dead or points to the wrong content
- the scraper generates broken output
- automation, releases, or validation reports are wrong

## Local checks

Run these before opening a PR:

```bash
python -m compileall -q .
python -m unittest discover -s tests
python tests/verify_artifacts.py
```

For a bounded scraper smoke test:

```bash
tmpdir=$(mktemp -d)
python scraper/main.py \
  --no-validate \
  --no-radiobrowser \
  --country "United Kingdom" \
  --output "$tmpdir/live_streams.sii" \
  --json "$tmpdir/live_streams.json" \
  --report "$tmpdir/VALIDATION.md" \
  --stations "$tmpdir/STATIONS.md"
python tests/verify_artifacts.py \
  "$tmpdir/live_streams.sii" \
  "$tmpdir/live_streams.json" \
  1
```

Optional checks:

```bash
uvx ruff check .
uvx bandit -q -r . -x ./.git
```

## Generated files

`live_streams.sii`, `live_streams.json`, `STATIONS.md`, and `VALIDATION.md` are generated artifacts. Prefer changing the scraper or upstream data sources rather than editing generated files by hand.

If a PR intentionally updates generated station data, include all generated artifacts together and run `python tests/verify_artifacts.py`.

## Security

Do not open public issues for vulnerabilities. Use the private reporting process described in [SECURITY.md](SECURITY.md).
