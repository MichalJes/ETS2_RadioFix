#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))

import radiobrowser
from formatter import write_json, write_report, write_sii, write_stations_md
from validator import validate

from scraper import fetch_stations

DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "live_streams.sii")
DEFAULT_JSON = os.path.join(os.path.dirname(__file__), "..", "live_streams.json")
DEFAULT_REPORT = os.path.join(os.path.dirname(__file__), "..", "VALIDATION.md")
DEFAULT_STATIONS = os.path.join(os.path.dirname(__file__), "..", "STATIONS.md")


def main():
    parser = argparse.ArgumentParser(description="ETS2 Radio station scraper & validator")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Path to output .sii file")
    parser.add_argument("--json", default=DEFAULT_JSON, help="Path to output .json file")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Path to validation report .md")
    parser.add_argument("--stations", default=DEFAULT_STATIONS, help="Path to STATIONS.md")
    parser.add_argument("--no-validate", action="store_true", help="Skip stream URL validation")
    parser.add_argument("--country", help="Filter to a single country (e.g. 'Poland')")
    parser.add_argument("--no-fandom", action="store_true", help="Skip the Fandom wiki source")
    parser.add_argument("--allow-partial", action="store_true",
                        help="Allow output when one enabled source fails")
    parser.add_argument("--no-radiobrowser", action="store_true",
                         help="Skip the Radio-Browser API source")
    parser.add_argument("--radiobrowser-limit", type=int, default=1000,
                         help="Max stations to pull from Radio-Browser (default: 1000)")
    args = parser.parse_args()

    if args.no_fandom and args.no_radiobrowser:
        parser.error("At least one station source must be enabled")
    stations = []
    source_errors = []
    empty_source_errors = []
    if not args.no_fandom:
        print("Fetching stations from Fandom wiki...")
        try:
            stations = fetch_stations()
            print(f"  Found {len(stations)} stations across all countries")
            if not stations:
                empty_source_errors.append("Fandom returned no stations")
        except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            source_errors.append(f"Fandom: {e}")
            print(f"  Fandom fetch failed: {e}")

    if not args.no_radiobrowser:
        print("Fetching stations from Radio-Browser API...")
        try:
            rb_stations = radiobrowser.fetch_stations(limit=args.radiobrowser_limit)
            print(f"  Found {len(rb_stations)} stations")
            if not rb_stations:
                empty_source_errors.append("Radio-Browser returned no stations")
        except RuntimeError as e:
            source_errors.append(f"Radio-Browser: {e}")
            print(f"  Radio-Browser fetch failed: {e}")
            rb_stations = []

        seen = {s.url for s in stations}
        new = [s for s in rb_stations if s.url not in seen]
        stations.extend(new)
        print(f"  Added {len(new)} new stations not already in the Fandom set")

    if empty_source_errors:
        parser.error("Enabled source returned no stations; existing output files were preserved: "
                     + "; ".join(empty_source_errors))
    if source_errors and not args.allow_partial:
        parser.error("Source fetch failed; use --allow-partial to permit partial output: "
                     + "; ".join(source_errors))
    if not stations:
        parser.error("No stations fetched; existing output files were preserved")

    if args.country:
        stations = [s for s in stations if s.country.lower() == args.country.lower()]
        print(f"  Filtered to {len(stations)} stations for '{args.country}'")

    if not args.no_validate:
        checked = [0]
        total = len(stations)

        def progress(url, alive):
            checked[0] += 1
            status = "OK " if alive else "DEAD"
            print(f"  [{checked[0]:>3}/{total}] {status}  {url[:70]}", flush=True)

        print(f"\nValidating {total} streams (this takes ~1-2 min)...")
        alive, dead = validate(stations, progress)
        print(f"\n  Live: {len(alive)}  |  Dead: {len(dead)}")

        report_path = os.path.abspath(args.report)
        write_report(alive, dead, report_path)
        print(f"  Report written: {report_path}")

        stations_path = os.path.abspath(args.stations)
        write_stations_md(alive, dead, stations_path)
        print(f"  Stations status written: {stations_path}")

        stations = alive
    else:
        print("Skipping validation.")

    out_path = os.path.abspath(args.output)
    write_sii(stations, out_path)
    json_path = os.path.abspath(args.json)
    write_json(stations, json_path)
    print(f"  JSON written: {json_path}")
    print(f"\nDone! {len(stations)} stations written to: {out_path}")


if __name__ == "__main__":
    main()
