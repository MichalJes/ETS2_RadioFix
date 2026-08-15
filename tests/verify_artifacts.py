#!/usr/bin/env python3
"""Verify live_streams.sii and live_streams.json stay in sync."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load_sii_entries(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    declared_match = re.search(r"^ stream_data:\s+(\d+)", text, re.MULTILINE)
    if not declared_match:
        raise AssertionError(f"{path}: missing stream_data count")

    declared = int(declared_match.group(1))
    entries = []
    for match in re.finditer(r'^ stream_data\[(\d+)\]: "(.*)"$', text, re.MULTILINE):
        index = int(match.group(1))
        parts = match.group(2).split("|")
        if len(parts) != 6:
            raise AssertionError(f"{path}: entry {index} has {len(parts)} pipe fields")
        entries.append(
            {
                "index": index,
                "url": parts[0],
                "name": parts[1],
                "genre": parts[2],
                "country_code": parts[3],
                "bit_rate": int(parts[4]),
                "playing": int(parts[5]),
            }
        )

    if declared != len(entries):
        raise AssertionError(f"{path}: declared {declared} entries but found {len(entries)}")
    if [entry["index"] for entry in entries] != list(range(len(entries))):
        raise AssertionError(f"{path}: stream_data indices are not contiguous from zero")
    return entries


def verify(sii_path: Path, json_path: Path, min_count: int = 0) -> None:
    sii_entries = load_sii_entries(sii_path)
    json_entries = json.loads(json_path.read_text(encoding="utf-8"))

    if len(sii_entries) < min_count:
        raise AssertionError(
            f"{sii_path}: expected at least {min_count} entries but found {len(sii_entries)}"
        )
    if len(sii_entries) != len(json_entries):
        raise AssertionError(
            f"{json_path}: has {len(json_entries)} entries but {sii_path} has {len(sii_entries)}"
        )
    if sii_entries != json_entries:
        raise AssertionError(f"{json_path}: content does not match {sii_path}")


def main() -> int:
    sii_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("live_streams.sii")
    json_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("live_streams.json")
    min_count = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    verify(sii_path, json_path, min_count)
    print(f"OK: {sii_path} and {json_path} are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
