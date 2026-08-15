# Security Policy

## Supported versions

Only the latest commit on the default `master` branch is actively maintained. Generated station data is refreshed by scheduled pull requests.

## Reporting a vulnerability

If you discover a security vulnerability in this project, please **do not open a public issue**.

Instead, report it privately via [GitHub's private vulnerability reporting](https://github.com/MichalJes/ETS2_RadioFix/security/advisories/new).

Please include:

- a description of the vulnerability
- steps to reproduce
- affected file(s), workflow, or generated artifact(s)
- potential impact

You can expect an acknowledgement within 7 days.

## Scope

This project scrapes radio station data from the [Truck Simulator Fandom wiki](https://truck-simulator.fandom.com/wiki/Radio_Stations) and the [Radio-Browser](https://www.radio-browser.info/) directory, then writes generated `live_streams.sii`, `live_streams.json`, `STATIONS.md`, and `VALIDATION.md` files.

Security considerations include:

- **Generated file injection** — upstream station names, genres, countries, and URLs are untrusted. Text fields are stripped of pipe characters, quotes, and newlines before they are written to the `.sii` pipe-delimited format.
- **URL injection** — only `http` and `https` stream URLs are accepted. Malformed URLs, overlong URLs, fragments, SII-breaking characters, and local/private/link-local IP literal targets are rejected before generated output is written.
- **Validator SSRF hardening** — validation fetches untrusted stream URLs. Before each validation request, the validator rejects unsafe schemes, unsafe IP literals, hostnames resolving to loopback/private/link-local/reserved/multicast/unspecified addresses, mixed safe/unsafe DNS results, and unsafe redirect targets.
- **Generated artifact consistency** — CI checks that `live_streams.sii` and `live_streams.json` contain the same stations with contiguous indices.
- **Workflow permissions** — the scheduled update workflow uses repository write permissions so it can open and merge generated-data PRs. Treat changes to `.github/workflows/` as security-sensitive.

## Non-goals and known limitations

- The project validates whether streams are reachable; it does not verify station ownership, licensing, or broadcast content.
- Generated Markdown reports are intended for GitHub repository display, not for rendering inside privileged HTML contexts.
- The validator intentionally makes outbound requests to public radio stream hosts. The SSRF protections reduce CI risk but do not make arbitrary URL fetching risk-free.
