import json
import urllib.request
import urllib.parse
from scraper import Station, _validate_url, _sanitise_field, _resolve_lang

# Public mirrors of the community-run Radio-Browser directory (radio-browser.info).
# Tried in order; the API is read-only and requires no key.
# "all.api..." round-robins across whichever mirrors are currently healthy —
# individual mirror subdomains (de1, nl1, at1, ...) rotate over time and go stale,
# so it's listed first with a couple of known-stable mirrors as fallback.
API_SERVERS = [
    "https://all.api.radio-browser.info",
    "https://de2.api.radio-browser.info",
]

# countrycode (ISO 3166-1 alpha-2) -> display name, kept aligned with the
# country names already used by the Fandom wiki source so overlapping
# countries merge into the same STATIONS.md section instead of splitting.
COUNTRYCODE_TO_NAME = {
    "AZ": "Azerbaijan", "BE": "Belgium", "CA": "Canada", "CL": "Chile",
    "HR": "Croatia", "CZ": "Czechia", "DK": "Denmark", "FR": "France",
    "DE": "Germany", "IS": "Iceland", "IT": "Italy", "LV": "Latvia",
    "LT": "Lithuania", "LU": "Luxembourg", "NL": "Netherlands", "NO": "Norway",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "RU": "Russia",
    "RS": "Serbia", "SK": "Slovakia", "ES": "Spain", "SE": "Sweden",
    "CH": "Switzerland", "TR": "Türkiye", "UA": "Ukraine", "GB": "United Kingdom",
    "US": "United States", "MK": "North Macedonia", "NZ": "New Zealand",
    "PH": "Philippines", "EE": "Estonia", "FI": "Finland", "AT": "Austria",
    "HU": "Hungary", "BG": "Bulgaria",
}


def _country_name(countrycode: str, fallback: str) -> str:
    name = COUNTRYCODE_TO_NAME.get((countrycode or "").upper())
    if name:
        return name
    return fallback.strip() if fallback else "Unknown"


def _fetch_json(server: str, limit: int) -> list[dict]:
    params = {
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true",
        "limit": str(limit),
    }
    url = f"{server}/json/stations/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "ETS2RadioScraper/1.0")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def fetch_stations(limit: int = 1000) -> list[Station]:
    raw = None
    last_err = None
    for server in API_SERVERS:
        try:
            raw = _fetch_json(server, limit)
            break
        except Exception as e:
            last_err = e
    if raw is None:
        raise RuntimeError(f"All Radio-Browser mirrors failed: {last_err}")

    stations = []
    seen: set[str] = set()
    for entry in raw:
        raw_url = entry.get("url_resolved") or entry.get("url") or ""
        url = _validate_url(raw_url)
        if url is None or url in seen:
            continue
        seen.add(url)

        name = entry.get("name") or "Unknown"
        tags = (entry.get("tags") or "").split(",")
        genre = tags[0].strip() if tags and tags[0].strip() else "Various"
        language = (entry.get("language") or "").split(",")[0].strip() or "?"
        country = _country_name(entry.get("countrycode", ""), entry.get("country", ""))
        bitrate = entry.get("bitrate") or 128

        stations.append(Station(
            url=url,
            name=_sanitise_field(name),
            genre=_sanitise_field(genre),
            language=_resolve_lang(language, country),
            bitrate=int(bitrate) if bitrate else 128,
            country=_sanitise_field(country),
        ))
    return stations
