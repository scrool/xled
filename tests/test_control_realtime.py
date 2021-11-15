#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import unittest
import warnings
import io
import struct

from xled.compat import is_py2
from xled.control import ControlInterface


with warnings.catch_warnings():
    if is_py2:
        warnings.simplefilter("ignore", category=DeprecationWarning)
    import vcr


def make_solid_movie(num, r, g, b):
    pat = [struct.pack(">BBB", r, g, b)] * num
    movie = io.BytesIO()
    movie.write(b"".join(pat))
    movie.seek(0)
    return movie


class FakeUDPclient:
    """
    Fake UDP client to replace the real UDP client, to catch the socket traffic.
    """

    def __init__(self):
        self.data = False

    def send(self, data):
        self.data = data

    def retrieve_data(self):
        data = self.data
        self.data = False
        return data


class TestControlInterfaceRealtime(unittest.TestCase):
    """
    Tests for the realtime mode of the `xled.control` module.

    This code tests the UDP realtime protocols by replacing the UDPClient of
    the ControlInterface with a fake UDP client which instead just records
    the transfered data so it can be compared to the expected traffic.
    """

    def redirect_xled_socket_to_fake_client(self, ctr):
        self.fakeclient = FakeUDPclient()
        ctr._udpclient = self.fakeclient

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_realtime.yaml")
    def test_realtime_protocols(self):
        num_leds = 250
        ctr = ControlInterface("192.168.10.100")
        ctr.set_mode("rt")

        # Restful realtime protocol
        ctr.set_rt_frame_rest(make_solid_movie(num_leds, 0, 255, 0))

        # Must be here (not in setUp), since it needs ctr
        self.redirect_xled_socket_to_fake_client(ctr)

        # Version 1 socket realtime protocol
        ctr.set_rt_frame_socket(
            make_solid_movie(num_leds, 230, 170, 0), 1, min(255, num_leds)
        )
        self.assertEqual(
            self.fakeclient.retrieve_data(),
            b'\x010"\x06\x04]j&X\xfa' + b"\xe6\xaa\x00" * num_leds,
        )

        # Version 2 socket realtime protocol
        ctr.set_rt_frame_socket(make_solid_movie(num_leds, 100, 255, 0), 2)
        self.assertEqual(
            self.fakeclient.retrieve_data(),
            b'\x020"\x06\x04]j&X\x00' + b"d\xff\x00" * num_leds,
        )

        # Version 3 socket realtime protocol
        ctr.set_rt_frame_socket(make_solid_movie(num_leds, 230, 85, 0), 3)
        self.assertEqual(
            self.fakeclient.retrieve_data(),
            b'\x030"\x06\x04]j&X\x00\x00\x00' + b"\xe6U\x00" * num_leds,
        )
