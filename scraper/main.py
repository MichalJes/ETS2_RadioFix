#!/usr/bin/env python3
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from scraper import fetch_stations
from validator import validate
from formatter import write_sii, write_report

DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "live_streams.sii")
DEFAULT_REPORT = os.path.join(os.path.dirname(__file__), "..", "VALIDATION.md")


def main():
    parser = argparse.ArgumentParser(description="ETS2 Radio station scraper & validator")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Path to output .sii file")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Path to validation report .md")
    parser.add_argument("--no-validate", action="store_true", help="Skip stream URL validation")
    parser.add_argument("--country", help="Filter to a single country (e.g. 'Poland')")
    args = parser.parse_args()

    print("Fetching stations from Fandom wiki...")
    stations = fetch_stations()
    print(f"  Found {len(stations)} stations across all countries")

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
        stations = alive
    else:
        print("Skipping validation.")

    out_path = os.path.abspath(args.output)
    write_sii(stations, out_path)
    print(f"\nDone! {len(stations)} stations written to: {out_path}")


if __name__ == "__main__":
    main()
