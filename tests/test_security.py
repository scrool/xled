from __future__ import absolute_import

import unittest

from xled import security


class TestXorStrings(unittest.TestCase):
    """Tests for `xled.security` module."""

    def test_identity(self):
        mac_packed = b"\\\xcf\x7f\xa1#K"
        key = b"\x00" * len(mac_packed)
        cipher = security.xor_strings(mac_packed, key)
        assert mac_packed == cipher

    def test_plus_one(self):
        mac_packed = b"\\\xcf\x7f\xa1#K"
        key = b"\x01" * len(mac_packed)
        cipher = security.xor_strings(mac_packed, key)
        assert b']\xce~\xa0"J' == cipher

    def test_short_identity(self):
        mac_packed = b"\\\xcf\x7f\xa1#K"
        cipher = security.xor_strings(mac_packed, b"\x00")
        assert mac_packed == cipher

    def test_short_plus_one(self):
        mac_packed = b"\\\xcf\x7f\xa1#K"
        cipher = security.xor_strings(mac_packed, b"\x01")
        assert b']\xce~\xa0"J' == cipher

    def test_invalid_message_none(self):
        with self.assertRaises(TypeError):
            security.xor_strings(None, b"\x01")

    def test_invalid_key_none(self):
        mac_packed = b"\\\xcf\x7f\xa1#K"
        with self.assertRaises(TypeError):
            security.xor_strings(mac_packed, None)

    def test_invalid_both_none(self):
        with self.assertRaises(TypeError):
            security.xor_strings(None, None)
