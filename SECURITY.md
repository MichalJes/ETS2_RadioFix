# Security Policy

## Supported versions

Only the latest commit on `master` is actively maintained.

## Reporting a vulnerability

If you discover a security vulnerability in this project, please **do not open a public issue**.

Instead, report it privately via [GitHub's private vulnerability reporting](https://github.com/MichalJes/ETS2_RadioFix/security/advisories/new).

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You can expect an acknowledgement within 7 days.

## Scope

This project scrapes radio station data from the [Truck Simulator Fandom wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations) and writes it into a game configuration file (`live_streams.sii`). Security considerations include:

- **URL injection** — malicious URLs committed to the wiki could end up in the output file. The scraper validates all URLs (scheme allowlist, length cap, format check) before writing them.
- **Field injection** — pipe characters and quotes are stripped from station names and genres to prevent breaking the `.sii` format.
