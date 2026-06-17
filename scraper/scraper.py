import re
import json
import urllib.request
from dataclasses import dataclass

FANDOM_API = (
    "https://truck-simulator.fandom.com/api.php"
    "?action=parse&page=Radio_Stations&prop=wikitext&format=json"
)

LANGUAGE_TO_ISO = {
    "english": "ENG", "dutch": "NLD", "french": "FRA", "german": "DEU",
    "polish": "POL", "czech": "CZE", "slovak": "SVK", "hungarian": "HUN",
    "romanian": "RON", "bulgarian": "BUL", "russian": "RUS", "ukrainian": "UKR",
    "lithuanian": "LIT", "latvian": "LAV", "estonian": "EST", "finnish": "FIN",
    "swedish": "SWE", "norwegian": "NOR", "danish": "DAN", "icelandic": "ISL",
    "spanish": "SPA", "portuguese": "POR", "italian": "ITA", "croatian": "HRV",
    "serbian": "SRB", "macedonian": "MKD", "turkish": "TUR", "azerbaijani": "AZE",
    "filipino": "FIL", "tagalog": "FIL", "various": "INT", "international": "INT",
    "multiple": "INT",
}

COUNTRY_TO_ISO = {
    "azerbaijan": "AZE", "belgium": "BEL", "canada": "CAN", "chile": "CHL",
    "croatia": "HRV", "czechia": "CZE", "czech republic": "CZE", "denmark": "DEN",
    "france": "FRA", "germany": "DEU", "iceland": "ISL", "italy": "ITA",
    "latvia": "LAV", "lithuania": "LIT", "luxembourg": "LUX", "netherlands": "NLD",
    "norway": "NOR", "poland": "POL", "portugal": "POR", "romania": "ROU",
    "russia": "RUS", "serbia": "SRB", "slovakia": "SVK", "spain": "ESP",
    "sweden": "SWE", "switzerland": "CHE", "turkey": "TUR", "türkiye": "TUR",
    "ukraine": "UKR", "united kingdom": "GBR", "united states": "USA",
    "north macedonia": "MKD", "new zealand": "NZL", "philippines": "PHL",
    "estonia": "EST", "finland": "FIN", "austria": "AUT", "hungary": "HUN",
    "bulgaria": "BGR",
}


@dataclass
class Station:
    url: str
    name: str
    genre: str
    language: str
    bitrate: int
    country: str


def _clean(text: str) -> str:
    text = re.sub(r"<nowiki>(.*?)</nowiki>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", text)
    # Extract URL from broken wiki-link format: [https: / host path |https://...]
    text = re.sub(r"\[https?:[^|]+\|(https?://[^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://(\S+)\s+[^\]]+\]", r"https://\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)
    return text.strip()


def _extract_url(text: str) -> str | None:
    m = re.search(r"https?://\S+", text)
    return m.group(0).rstrip(".,;)") if m else None


def _resolve_lang(language: str, country: str) -> str:
    lang = language.lower().strip()
    if lang in ("?", "", "unknown", "n/a"):
        return COUNTRY_TO_ISO.get(country.lower(), "INT")
    return LANGUAGE_TO_ISO.get(lang, lang[:3].upper())


def _parse_bitrate(value: str) -> int:
    try:
        return int(re.search(r"\d+", value).group())
    except (AttributeError, ValueError):
        return 128


# Header keywords that identify each column type
_URL_HEADERS = {"link", "stream", "url"}
_NAME_HEADERS = {"radio station", "station", "name"}
_GENRE_HEADERS = {"genre", "genge"}
_LANG_HEADERS = {"language"}
_BITRATE_HEADERS = {"bitrate"}


def _header_type(h: str) -> str:
    h = h.lower().strip().lstrip("!")
    if h in _URL_HEADERS:
        return "url"
    if h in _NAME_HEADERS:
        return "name"
    if h in _GENRE_HEADERS:
        return "genre"
    if h in _LANG_HEADERS:
        return "lang"
    if h in _BITRATE_HEADERS:
        return "bitrate"
    return "other"


def _parse_table(table_text: str, country: str) -> list[Station]:
    stations = []
    rows = re.split(r"\n\|-", table_text)

    # Parse header row to build column map (0-indexed relative to data cells)
    col_map: dict[int, str] = {}
    for row in rows[:2]:
        if "!" in row:
            headers = re.split(r"\n[|!]", row)
            # Skip first element (table declaration like "{| class=...")
            data_headers = [h for h in headers[1:] if _clean(h) not in ("", "-", "+")]
            for idx, h in enumerate(data_headers):
                t = _header_type(_clean(h))
                if t != "other":
                    col_map[idx] = t
            break

    for row in rows[1:]:
        raw_cells = re.split(r"\n[|!](?!\|)", row)
        cells = [_clean(c) for c in raw_cells if c.strip() not in ("", "-", "+")]
        if len(cells) < 2:
            continue

        # Find URL: first try column map, then scan all cells
        url = None
        name = None
        genre = "Various"
        language = "?"
        bitrate_raw = "128"

        if col_map:
            by_type: dict[str, str] = {}
            for idx, cell in enumerate(cells):
                ctype = col_map.get(idx, "other")
                if ctype not in by_type:
                    by_type[ctype] = cell
            url_cell = by_type.get("url", "")
            url = _extract_url(url_cell) or (url_cell if url_cell.startswith("http") else None)
            name = by_type.get("name")
            genre = by_type.get("genre", "Various") or "Various"
            language = by_type.get("lang", "?")
            bitrate_raw = by_type.get("bitrate", "128")

        if url is None:
            # Fallback: scan cells for a URL
            for i, cell in enumerate(cells):
                u = _extract_url(cell)
                if u:
                    url = u
                    # best guess: adjacent non-URL cell is the name
                    name = cells[i - 1] if i > 0 else (cells[i + 1] if i + 1 < len(cells) else "Unknown")
                    break

        if url is None:
            continue
        if name is None:
            name = "Unknown"
        if genre in ("?", ""):
            genre = "Various"

        stations.append(Station(
            url=url,
            name=name,
            genre=genre,
            language=_resolve_lang(language, country),
            bitrate=_parse_bitrate(bitrate_raw),
            country=country,
        ))
    return stations


SKIP_SECTIONS = {
    "editing live_streams.sii file manually", "radio stations by country",
    "dead streams", "graphical alternative"
}

# Sub-sections that belong to a parent country
SECTION_PARENT = {
    "global player": "United Kingdom",
    "bbc radio": "United Kingdom",
    "türkiye": "Türkiye",  # normalise heading encoding
}


def fetch_stations() -> list[Station]:
    req = urllib.request.Request(FANDOM_API)
    req.add_header("User-Agent", "Mozilla/5.0 (compatible; ETS2RadioScraper/1.0)")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    wikitext = data["parse"]["wikitext"]["*"]

    # Split on === or == headings; result: [pre, heading, content, heading, content, ...]
    parts = re.split(r"={2,3}([^=\n]+?)={2,3}", wikitext)

    stations = []
    for i in range(1, len(parts) - 1, 2):
        raw_heading = parts[i]
        content = parts[i + 1]
        country = re.sub(r"'{2,}", "", raw_heading).strip()
        country = SECTION_PARENT.get(country.lower(), country)
        if country.lower() in SKIP_SECTIONS:
            continue
        tables = re.findall(r"\{\|.*?\|\}", content, re.DOTALL)
        for table in tables:
            stations.extend(_parse_table(table, country))

    seen: set[str] = set()
    unique = []
    for s in stations:
        if s.url not in seen:
            seen.add(s.url)
            unique.append(s)
    return unique
