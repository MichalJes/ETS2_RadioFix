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


def _connect_public(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Resolve once, validate every answer, then connect using its numeric sockaddr."""
    host, port = address
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses or any(_is_blocked_ip(str(item[4][0])) for item in addresses):
        raise OSError("Unsafe stream address")
    last_error = None
    for family, socktype, proto, _, sockaddr in addresses:
        sock = socket.socket(family, socktype, proto)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_error = exc
            sock.close()
    raise last_error or OSError("No usable stream address")


def _urlopen(req: urllib.request.Request, timeout: int):
    # Direct connections are intentional: a proxy would resolve the target itself,
    # outside our address validation. HTTPSConnection retains hostname TLS checks.
    url = req.full_url
    method = req.get_method()
    for _ in range(11):
        if _validate_url(url) is None:
            raise ValueError("Unsafe stream URL")
        parsed = urllib.parse.urlsplit(url)
        cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = cls(parsed.hostname, parsed.port, timeout=timeout)
        connection._create_connection = _connect_public
        try:
            path = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
            headers = dict(req.header_items())
            headers["Connection"] = "close"
            connection.request(method, path, headers=headers)
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308) and response.getheader("Location"):
                url = urllib.parse.urljoin(url, response.getheader("Location"))
                response.close()
                connection.close()
                if response.status == 303 and method != "HEAD":
                    method = "GET"
                continue
            if response.status >= 400:
                status = response.status
                response.close()
                connection.close()
                raise urllib.error.HTTPError(url, status, "Stream request failed", {}, None)
            return response
        except Exception:
            connection.close()
            raise
    raise urllib.error.HTTPError(url, 310, "Too many redirects", {}, None)


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
