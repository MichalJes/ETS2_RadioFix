from __future__ import annotations

import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scraper"))

from validator import _is_safe_fetch_url


class SafeFetchUrlTests(unittest.TestCase):
    def test_rejects_private_hostname_resolution(self) -> None:
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, None, None, None, ("10.0.0.10", 0))]):
            self.assertFalse(_is_safe_fetch_url("https://radio.example/stream"))

    def test_rejects_loopback_hostname_resolution(self) -> None:
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, None, None, None, ("127.0.0.1", 0))]):
            self.assertFalse(_is_safe_fetch_url("https://localhost.example/stream"))

    def test_accepts_public_hostname_resolution(self) -> None:
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, None, None, None, ("93.184.216.34", 0))]):
            self.assertTrue(_is_safe_fetch_url("https://radio.example/stream"))

    def test_rejects_mixed_public_and_private_resolution(self) -> None:
        answers = [
            (socket.AF_INET, None, None, None, ("93.184.216.34", 0)),
            (socket.AF_INET, None, None, None, ("192.168.1.10", 0)),
        ]
        with patch.object(socket, "getaddrinfo", return_value=answers):
            self.assertFalse(_is_safe_fetch_url("https://radio.example/stream"))


if __name__ == "__main__":
    unittest.main()
