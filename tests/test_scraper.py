from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scraper"))

from scraper import _sanitise_field, _validate_url


class UrlValidationTests(unittest.TestCase):
    def test_accepts_normal_http_and_https_stream_urls(self) -> None:
        self.assertEqual(_validate_url("https://example.com/stream.mp3"), "https://example.com/stream.mp3")
        self.assertEqual(_validate_url("http://radio.example.org:8000/live"), "http://radio.example.org:8000/live")

    def test_rejects_sii_breaking_characters(self) -> None:
        self.assertIsNone(_validate_url('https://example.com/stream"bad'))
        self.assertIsNone(_validate_url("https://example.com/stream|bad"))
        self.assertIsNone(_validate_url("https://example.com/stream\nbad"))

    def test_rejects_non_http_schemes_and_missing_hosts(self) -> None:
        self.assertIsNone(_validate_url("file:///etc/passwd"))
        self.assertIsNone(_validate_url("ftp://example.com/stream"))
        self.assertIsNone(_validate_url("https:///missing-host"))

    def test_strips_fragments(self) -> None:
        self.assertEqual(
            _validate_url("https://example.com/stream.mp3#AddedBySomeone"),
            "https://example.com/stream.mp3",
        )

    def test_rejects_local_and_private_ip_literal_targets(self) -> None:
        for url in [
            "http://127.0.0.1:8000/stream",
            "http://[::1]:8000/stream",
            "http://10.0.0.1/stream",
            "http://172.16.0.1/stream",
            "http://192.168.1.1/stream",
            "http://169.254.169.254/latest/meta-data/",
        ]:
            with self.subTest(url=url):
                self.assertIsNone(_validate_url(url))


class FieldSanitisationTests(unittest.TestCase):
    def test_strips_sii_delimiters_from_text_fields(self) -> None:
        self.assertEqual(_sanitise_field('Name|with"bad\nchars'), "Name with bad chars")

    def test_caps_field_length(self) -> None:
        self.assertEqual(len(_sanitise_field("x" * 200)), 128)


if __name__ == "__main__":
    unittest.main()
