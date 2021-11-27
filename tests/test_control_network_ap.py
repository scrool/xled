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


class TestControlInterfaceNetworkAP(unittest.TestCase):
    """
    Tests setting network mode to Access point. Assumes that the device is
    initially in Station network mode.
    """

    def setUp(self):
        self.host = "192.168.10.100"
        self.numleds = 250
        self.ledbytes = 3
        self.isrecording = False

    def assertEqualSubdict(self, values, subdict):
        for key in subdict:
            self.assertIn(key, values)
            self.assertEqual(values[key], subdict[key])

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_network_mode_ap.yaml")
    def test_network_mode_ap(self):
        ctr = ControlInterface(self.host)

        res = ctr.get_network_status()._data
        if self.isrecording:
            print("get_network_status:", res)
        else:
            self.assertEqual(
                res,
                {
                    "mode": 1,
                    "station": {
                        "ssid": "MyWiFi",
                        "ip": "192.168.10.100",
                        "gw": "192.168.10.1",
                        "mask": "255.255.255.0",
                        "rssi": -60,
                    },
                    "ap": {
                        "ssid": "Twinkly_ABCDEF",
                        "channel": 1,
                        "ip": "192.168.4.1",
                        "enc": 4,
                        "ssid_hidden": 0,
                        "max_connections": 4,
                        "password_changed": 1,
                    },
                    "code": 1000,
                },
            )

        res = ctr.set_network_mode_ap()._data
        if self.isrecording:
            print("set_network_mode_ap:", res)
        else:
            self.assertEqual(res, {"code": 1000})
