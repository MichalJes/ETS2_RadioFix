import asyncio
import urllib.request
import urllib.error
from scraper import Station

TIMEOUT = 6
CONCURRENCY = 30


def _check(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "ETS2RadioScraper/1.0")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status < 400
    except Exception:
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "ETS2RadioScraper/1.0")
            req.add_header("Range", "bytes=0-0")
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status < 400
        except Exception:
            return False


async def _check_async(url: str, sem: asyncio.Semaphore) -> tuple[str, bool]:
    async with sem:
        loop = asyncio.get_event_loop()
        alive = await loop.run_in_executor(None, _check, url)
        return url, alive


async def _validate_all(urls: list[str], progress_cb) -> dict[str, bool]:
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [_check_async(url, sem) for url in urls]
    results = {}
    for coro in asyncio.as_completed(tasks):
        url, alive = await coro
        results[url] = alive
        progress_cb(url, alive)
    return results


def validate(stations: list[Station], progress_cb=None) -> tuple[list[Station], list[Station]]:
    if progress_cb is None:
        progress_cb = lambda url, alive: None
    urls = [s.url for s in stations]
    results = asyncio.run(_validate_all(urls, progress_cb))
    alive = [s for s in stations if results.get(s.url, False)]
    dead = [s for s in stations if not results.get(s.url, False)]
    return alive, dead
