import contextlib
import http.client
import io
import socket
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scraper'))
import main
import validator
from scraper import Station, _parse_table, _validate_url


class ParserRegressionTests(unittest.TestCase):
    def test_blank_cell_preserves_column_alignment(self):
        table = '''{| class="wikitable"
! Radio station
! Link
! Genre
! Language
! Bitrate
|-
| Example Radio
| https://example.org/live
|
| English
| 192
|}'''
        station, = _parse_table(table, 'United Kingdom')
        self.assertEqual((station.name, station.genre, station.language, station.bitrate),
                         ('Example Radio', 'Various', 'ENG', 192))

    def test_invalid_ports_are_rejected_without_aborting_validation(self):
        for port in ('bad', '65536', '-1'):
            url = f'http://example.org:{port}/live'
            self.assertIsNone(_validate_url(url))
            self.assertFalse(validator._check(url))


class ConnectionRegressionTests(unittest.TestCase):
    def test_socket_uses_checked_address_without_second_resolution(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]
        private = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))]
        with patch('validator.socket.getaddrinfo', side_effect=[public, private]) as dns, \
                patch('validator.socket.socket') as socket_factory:
            validator._connect_public(('radio.example', 80), 6)
            dns.assert_called_once()
            socket_factory.return_value.connect.assert_called_once_with(('93.184.216.34', 80))

    def test_mixed_dns_answers_never_open_socket(self):
        answers = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 80))
                   for ip in ('93.184.216.34', '10.0.0.1')]
        with patch('validator.socket.getaddrinfo', return_value=answers), \
                patch('validator.socket.socket') as socket_factory:
            with self.assertRaises(OSError):
                validator._connect_public(('radio.example', 80), 6)
            socket_factory.assert_not_called()

    def test_https_wraps_pinned_socket_with_original_hostname(self):
        connection = http.client.HTTPSConnection('radio.example')
        connection._create_connection = validator._connect_public
        raw_socket = MagicMock()
        with patch('validator.socket.getaddrinfo', return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]), \
                patch('validator.socket.socket', return_value=raw_socket), \
                patch.object(connection._context, 'wrap_socket') as tls:
            connection.connect()
            tls.assert_called_once_with(raw_socket, server_hostname='radio.example')
            self.assertTrue(connection._context.check_hostname)
            connection.close()

    def test_http_request_uses_pinned_socket_and_reads_real_response(self):
        sock = MagicMock()
        sock.makefile.return_value = io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
        with patch('validator.socket.getaddrinfo', return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]), \
                patch('validator.socket.socket', return_value=sock):
            with validator._urlopen(urllib.request.Request('http://radio.example/live'), 6) as response:
                self.assertEqual(response.status, 200)
            sock.connect.assert_called_once_with(('93.184.216.34', 80))
            request = sock.sendall.call_args.args[0]
            self.assertIn(b'Host: radio.example', request)
            self.assertIn(b'GET /live HTTP/1.1', request)

    def test_redirect_to_private_ip_is_rejected(self):
        with patch('validator.http.client.HTTPConnection') as factory:
            response = factory.return_value.getresponse.return_value
            response.status = 302
            response.getheader.return_value = 'http://127.0.0.1/internal'
            with self.assertRaises(ValueError):
                validator._urlopen(urllib.request.Request('http://radio.example/live'), 6)
            factory.assert_called_once()
            factory.return_value.close.assert_called()

    def test_head_error_falls_back_to_get(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch('validator._is_safe_fetch_url', return_value=True), \
                patch('validator._urlopen', side_effect=[
                    urllib.error.HTTPError('http://radio.example', 405, 'Method', {}, None), response
                ]) as fetch:
            self.assertTrue(validator._check('http://radio.example/live'))
            self.assertEqual([call.args[0].get_method() for call in fetch.call_args_list], ['HEAD', 'GET'])


class SourceRegressionTests(unittest.TestCase):
    def invoke(self, directory, *options):
        paths = [str(Path(directory) / name) for name in ('streams.sii', 'streams.json')]
        argv = ['main.py', '--no-validate', '--output', paths[0], '--json', paths[1], *options]
        with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            main.main()
        return paths

    def test_explicit_radio_browser_only_writes_valid_artifacts(self):
        from verify_artifacts import verify
        with tempfile.TemporaryDirectory() as directory, \
                patch('main.fetch_stations') as fandom, \
                patch('main.radiobrowser.fetch_stations', return_value=[
                    Station('https://example.org/live', 'Radio', 'Rock', 'ENG', 192, 'UK')]):
            paths = self.invoke(directory, '--no-fandom')
            fandom.assert_not_called()
            verify(Path(paths[0]), Path(paths[1]), 1)

    def test_source_failure_requires_explicit_partial_opt_in(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch('main.fetch_stations', side_effect=OSError('source unavailable')), \
                patch('main.radiobrowser.fetch_stations', return_value=[
                    Station('https://example.org/live', 'Radio', 'Rock', 'ENG', 192, 'UK')]) as radio:
            output = Path(directory) / 'streams.sii'
            output.write_text('existing data')
            with self.assertRaises(SystemExit):
                self.invoke(directory)
            self.assertEqual(output.read_text(), 'existing data')
            radio.assert_called_once()
            self.invoke(directory, '--allow-partial')
            self.assertIn('Radio', output.read_text())

    def test_empty_sources_preserve_outputs_even_with_partial_opt_in(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch('main.fetch_stations', side_effect=OSError('source unavailable')), \
                patch('main.radiobrowser.fetch_stations', return_value=[]):
            with self.assertRaises(SystemExit):
                self.invoke(directory, '--allow-partial')
            self.assertFalse((Path(directory) / 'streams.sii').exists())

    def test_empty_fandom_source_fails_even_when_radio_browser_has_data(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch('main.fetch_stations', return_value=[]), \
                patch('main.radiobrowser.fetch_stations', return_value=[
                    Station('https://example.org/live', 'Radio', 'Rock', 'ENG', 192, 'UK')]):
            output = Path(directory) / 'streams.sii'
            output.write_text('existing data')
            with self.assertRaises(SystemExit):
                self.invoke(directory, '--allow-partial')
            self.assertEqual(output.read_text(), 'existing data')

    def test_empty_radio_browser_source_fails_even_when_fandom_has_data(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch('main.fetch_stations', return_value=[
                    Station('https://example.org/wiki', 'Wiki Radio', 'Rock', 'ENG', 192, 'UK')]), \
                patch('main.radiobrowser.fetch_stations', return_value=[]):
            output = Path(directory) / 'streams.sii'
            output.write_text('existing data')
            with self.assertRaises(SystemExit):
                self.invoke(directory, '--allow-partial')
            self.assertEqual(output.read_text(), 'existing data')
