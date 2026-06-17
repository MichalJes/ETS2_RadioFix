import re
import json

with open("live_streams.sii", "r") as inFile:
    file = inFile.read()

lines = file.split("\n")
stations = []

for line in lines:
    match = re.search(r"stream_data\[(\d+)\]: \"(.*)\"", line)

    if match:
        index = match.group(1)
        info = match.group(2)
        parts = info.split("|")
        station = {
            "index": int(index),
            "url": parts[0],
            "name": parts[1],
            "genre": parts[2],
            "country_code": parts[3],
            "bit_rate": int(parts[4]),
            "playing": int(parts[5])
        }
        stations.append(station)

with open("live_streams.json", "w") as outFile:
    json.dump(stations, outFile)
