from scraper import Station

HEADER = "SiiNunit\n{\nlive_stream_def : _nameless.294.f89b.cca0 {\n"
FOOTER = "}\n\n}\n"


def write_sii(stations: list[Station], path: str) -> None:
    lines = [HEADER]
    lines.append(f" stream_data: {len(stations)}\n")
    for i, s in enumerate(stations):
        name = s.name.replace('"', "'")
        genre = s.genre.replace('"', "'")
        lang = s.language[:3].upper()
        line = f' stream_data[{i}]: "{s.url}|{name}|{genre}|{lang}|{s.bitrate}|0"\n'
        lines.append(line)
    lines.append(FOOTER)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def write_report(alive: list[Station], dead: list[Station], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Validation Report\n\n")
        f.write(f"**Live:** {len(alive)}  |  **Dead:** {len(dead)}\n\n")
        if dead:
            f.write("## Dead streams\n\n")
            f.write("| Station | URL | Country |\n|---|---|---|\n")
            for s in sorted(dead, key=lambda x: x.country):
                f.write(f"| {s.name} | {s.url} | {s.country} |\n")
