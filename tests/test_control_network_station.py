#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import unittest
import warnings

from xled.compat import is_py2
from xled.control import ControlInterface


with warnings.catch_warnings():
    if is_py2:
        warnings.simplefilter("ignore", category=DeprecationWarning)
    import vcr


class TestControlInterfaceNetworkStation(unittest.TestCase):
    """
    Tests setting network mode to Station. Assumes that the device is
    initially in AP network mode, and that it already has a configured
    wavelan ssid and password to connect with.
    """

    def setUp(self):
        self.hostap = "192.168.4.1"
        self.numleds = 250
        self.ledbytes = 3
        self.isrecording = False

    def assertEqualSubdict(self, values, subdict):
        for key in subdict:
            self.assertIn(key, values)
            self.assertEqual(values[key], subdict[key])

    @vcr.use_cassette(
        "tests/cassettes/TestControlInterface.test_network_mode_station.yaml"
    )
    def test_network_mode_station(self):
        ctr = ControlInterface(self.hostap)

        res = ctr.get_network_status()._data
        if self.isrecording:
            print("get_network_status:", res)
        else:
            self.assertEqual(
                res,
                {
                    "mode": 2,
                    "station": {
                        "ssid": "",
                        "ip": "0.0.0.0",
                        "gw": "0.0.0.0",
                        "mask": "0.0.0.0",
                    },
                    "ap": {
                        "ssid": "Twinkly_ABCDEF",
                        "channel": 6,
                        "ip": "192.168.4.1",
                        "enc": 3,
                        "ssid_hidden": 0,
                        "max_connections": 4,
                        "password_changed": 1,
                    },
                    "code": 1000,
                },
            )

        res = ctr.set_network_mode_station()._data
        if self.isrecording:
            print("set_network_mode_station:", res)
        else:
            self.assertEqual(res, {"code": 1000})
