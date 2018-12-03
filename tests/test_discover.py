from __future__ import absolute_import

import unittest

from xled import discover
from xled.compat import is_py3


class TestDiscovery(unittest.TestCase):
    """Tests for `xled.discovery` module."""

    def test_invalid_type_discovery_response1(self):
        with self.assertRaises(TypeError):
            discover.decode_discovery_response(None)

    def test_invalid_type_discovery_response2(self):
        with self.assertRaises(TypeError):
            discover.decode_discovery_response(list())


class TestDiscoveryString(unittest.TestCase):
    """Tests for `xled.discovery` module. String input data."""

    def test_valid_discovery_response(self):
        if is_py3:
            data = bytearray(b"\xab\x01\xa8\xc0OKTwinkly_A1234B\x00")
        else:
            data = "\xab\x01\xa8\xc0OKTwinkly_A1234B\x00"
        decoded = discover.decode_discovery_response(data)
        assert len(decoded) == 2
        part0, part1 = decoded
        assert part0 == b"192.168.1.171"
        assert part1 == b"Twinkly_A1234B"

    def test_invalid_status_discovery_response(self):
        if is_py3:
            data = bytearray(b"\xab\x01\xa8\xc0KOTwinkly_A1234B\x00")
        else:
            data = "\xab\x01\xa8\xc0KOTwinkly_A1234B\x00"
        with self.assertRaises(ValueError):
            discover.decode_discovery_response(data)

    def test_invalid_end_discovery_response(self):
        if is_py3:
            data = bytearray(b"\xab\x01\xa8\xc0OKTwinkly_A1234B\x01")
        else:
            data = "\xab\x01\xa8\xc0OKTwinkly_A1234B\x01"
        with self.assertRaises(ValueError):
            discover.decode_discovery_response(data)
