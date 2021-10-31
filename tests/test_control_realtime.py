#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import unittest
import warnings
import io
import struct
import time
from threading import Thread
import socket

from xled.compat import is_py2
from xled.control import ControlInterface


with warnings.catch_warnings():
    if is_py2:
        warnings.simplefilter("ignore", category=DeprecationWarning)
    import vcr


def make_solid_movie(num, r, g, b):
    pat = [struct.pack(">BBB", r, g, b)] * num
    movie = io.BytesIO()
    movie.write(b''.join(pat))
    movie.seek(0)
    return movie


class TestControlInterfaceRealtime(unittest.TestCase):
    """
    Tests for the realtime mode of the `xled.control` module.

    The recommended way to unit-test socket traffic is to replace the other
    end of the socket with a fake server or client. To do this, this code
    make assumptions about the internals of `xled.udp_client`. When that
    module is updated this test may need updates too. A complication is that
    the udp_client assumes communication between the same port on both the
    remote and local side, but during the test the fake server is also on the
    local machine, so another port number has to be used.
    """

    def run_fake_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.bind(('127.0.0.1', 7776))
        self.data = False
        data = self.sock.recv(10000)
        while len(data) > 0:
            self.data = data
            data = self.sock.recv(10000)

    def read_fake_server(self):
        while self.data is False:
            time.sleep(0.01)
        data = self.data
        self.data = False
        return data

    def close_fake_server(self, ctr):
        ctr.udpclient.send(b"")  # Tell fake server that data has ended
        self.sock.close()
        self.thread.join()

    def redirect_xled_socket_to_fake_server(self, ctr):
        ctr.udpclient.handle  # Triggers creation of socket in the ControlInterface
        ctr.udpclient.destination_host = "127.0.0.1"  # Redirect to localhost
        ctr.udpclient.port = 7776  # udp_client has already hogged 7777 on localhost, so use another port

    def setUp(self):
        self.thread = Thread(target=self.run_fake_server)
        self.thread.start()

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_realtime.yaml")
    def test_realtime_protocols(self):
        num_leds = 250
        ctr = ControlInterface("192.168.10.100")
        ctr.set_mode("rt")

        # Restful realtime protocol
        ctr.set_rt_frame_rest(make_solid_movie(num_leds, 0, 255, 0))

        # Must be here (not in setUp), since it needs ctr
        self.redirect_xled_socket_to_fake_server(ctr)

        # Version 1 socket realtime protocol
        ctr.set_rt_frame_socket(make_solid_movie(num_leds, 230, 170, 0), 1, min(255, num_leds))
        self.assertEqual(self.read_fake_server(), b'\x010"\x06\x04]j&X\xfa' + b'\xe6\xaa\x00' * num_leds)

        # Version 2 socket realtime protocol
        ctr.set_rt_frame_socket(make_solid_movie(num_leds, 100, 255, 0), 2)
        self.assertEqual(self.read_fake_server(), b'\x020"\x06\x04]j&X\x00' + b'd\xff\x00' * num_leds)

        # Version 3 socket realtime protocol
        ctr.set_rt_frame_socket(make_solid_movie(num_leds, 230, 85, 0), 3)
        self.assertEqual(self.read_fake_server(), b'\x030"\x06\x04]j&X\x00\x00\x00' + b'\xe6U\x00' * num_leds)

        # Again, is here (not in tearDown) since it needs ctr
        self.close_fake_server(ctr)
