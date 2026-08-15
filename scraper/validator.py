import asyncio
import http.client
import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request

from scraper import Station, _validate_url

TIMEOUT = 6
CONCURRENCY = 30


def _is_blocked_ip(ip_text: str) -> bool:
    ip = ipaddress.ip_address(ip_text)
    return any((
        ip.is_loopback,
        ip.is_private,
        ip.is_link_local,
        ip.is_multicast,
        ip.is_reserved,
        ip.is_unspecified,
    ))


def _is_safe_fetch_url(url: str) -> bool:
    """Return True when a stream URL is safe for the CI validator to fetch."""
    if _validate_url(url) is None:
        return False
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    if hostname is None:
        return False
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port, type=socket.SOCK_STREAM)
    except OSError:
        return False
    if not addresses:
        return False
    for *_, sockaddr in addresses:
        if _is_blocked_ip(str(sockaddr[0])):
            return False
    return True


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _is_safe_fetch_url(newurl):
            raise urllib.error.HTTPError(newurl, code, "Unsafe redirect target", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _urlopen(req: urllib.request.Request, timeout: int):
    opener = urllib.request.build_opener(_SafeRedirectHandler)
    return opener.open(req, timeout=timeout)


def _check(url: str) -> bool:
    if not _is_safe_fetch_url(url):
        return False
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "ETS2RadioScraper/1.0")
        with _urlopen(req, timeout=TIMEOUT) as r:
            return r.status < 400
    except (OSError, TimeoutError, urllib.error.URLError, ValueError, http.client.HTTPException):
        try:
            if not _is_safe_fetch_url(url):
                return False
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "ETS2RadioScraper/1.0")
            req.add_header("Range", "bytes=0-0")
            with _urlopen(req, timeout=TIMEOUT) as r:
                return r.status < 400
        except (OSError, TimeoutError, urllib.error.URLError, ValueError, http.client.HTTPException):
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
