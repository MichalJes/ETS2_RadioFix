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

This project scrapes radio station data from the [Truck Simulator Fandom wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations) and the [Radio-Browser](https://www.radio-browser.info/) directory, then writes generated `live_streams.sii`, `live_streams.json`, `STATIONS.md`, and `VALIDATION.md` files. Security considerations include:

- **URL injection** — malicious URLs committed to an upstream directory could end up in generated output. The scraper validates all URLs before writing them: only `http` and `https` schemes are allowed, URLs have a length cap, fragments are stripped, malformed URLs are rejected, and local/private/link-local IP literal targets are rejected.
- **Field injection** — pipe characters, quotes, and newlines are stripped from station names, genres, and country fields to prevent breaking the `.sii` pipe-delimited format.
- **Validator SSRF hardening** — validation fetches untrusted stream URLs. Before each validation request, the validator rejects unsafe schemes, local/private/link-local/reserved/multicast/unspecified IP targets, hostnames resolving to those ranges, and unsafe redirect targets.
- **Generated artifact consistency** — CI checks that `live_streams.sii` and `live_streams.json` contain the same stations and contiguous indices.

Known limitation: generated Markdown reports are intended for repository display, not for rendering inside privileged HTML contexts.
