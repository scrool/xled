from __future__ import absolute_import

import unittest

from xled import security


#: Test MAC address from xled-doc
MAC_ADDRESS_TEST = "5C:CF:7F:33:AA:FF"


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


class TestEncryptWiFiPassword(unittest.TestCase):
    """Tests for encrypt_wifi_password() from `xled.security` module."""

    def test_valid(self):
        expected_cipher = (
            b"e4XXiiUhg4J1FnJEfUQ0BhIji2HGVk1NHU5vGCHfyclF"
            b"dX6R8Nd9BSXVKS5nj2FXGU6SWv9CIzztfAvGgTGLUw=="
        )
        str_password = "Twinkly"
        cipher = security.encrypt_wifi_password(str_password, MAC_ADDRESS_TEST)
        assert expected_cipher == cipher
        bytes_password = b"Twinkly"
        cipher = security.encrypt_wifi_password(bytes_password, MAC_ADDRESS_TEST)
        assert expected_cipher == cipher


class TestEncryptWiFiCredentials(unittest.TestCase):
    """Tests for encrypt_wifi_credentials() from `xled.security` module."""

    def test_valid_legacy_key(self):
        expected_cipher = (
            b"e4XXiiUhg4J1FnJEfUQ0BhIji2HGVk1NHU5vGCHfyclF"
            b"dX6R8Nd9BSXVKS5nj2FXGU6SWv9CIzztfAvGgTGLUw=="
        )

        str_password = "Twinkly"
        cipher = security.encrypt_wifi_credentials(
            str_password, MAC_ADDRESS_TEST, security.SHARED_KEY_WIFI
        )
        assert expected_cipher == cipher
        bytes_password = b"Twinkly"
        cipher = security.encrypt_wifi_credentials(
            bytes_password, MAC_ADDRESS_TEST, security.SHARED_KEY_WIFI
        )
        assert expected_cipher == cipher

    def test_valid_v2_key(self):
        expected_cipher = (
            b"R8/Wb0N52RLRU9HAqutebsmJZrNwdMJPOzmXLk4+0cjU"
            b"TgXS/J+nZ9icDcTNb5P2Kb6TZP2TCNxpQGtnjetMrg=="
        )
        str_password = "Twinkly"
        cipher = security.encrypt_wifi_credentials(
            str_password, MAC_ADDRESS_TEST, security.SHARED_KEY_WIFI_V2
        )
        assert expected_cipher == cipher
        bytes_password = b"Twinkly"
        cipher = security.encrypt_wifi_credentials(
            bytes_password, MAC_ADDRESS_TEST, security.SHARED_KEY_WIFI_V2
        )
        assert expected_cipher == cipher


class TestDeriveKey(unittest.TestCase):
    """Tests for derive_key() from `xled.security` module."""

    def test_challenge_key(self):
        expected_secret_key = b"9\xb9\x1a]\xc7\x90.\xaa\x0cV\xc9\x8d9\xbb^\x12"
        assert expected_secret_key == security.derive_key(
            security.SHARED_KEY_CHALLANGE, MAC_ADDRESS_TEST
        )

    def test_wifi_key(self):
        expected_secret_key = b"/\xba\x0fV\xd8\x8c9\xac\rV\xde\x949\xb6^\x12"
        assert expected_secret_key == security.derive_key(
            security.SHARED_KEY_WIFI, MAC_ADDRESS_TEST
        )
