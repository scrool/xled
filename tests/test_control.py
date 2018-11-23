#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import vcr
import unittest

import xled.control


class TestControlInterface(unittest.TestCase):
    """Tests for `xled.control` module."""

    @vcr.use_cassette('tests/cassettes/TestControlInterface.test_mode_off.yaml')
    def test_mode_off(self):
        control_interface = xled.control.ControlInterface("192.168.1.171")
        control_interface.set_mode("off")
        response = control_interface.get_mode()
        assert "mode" in response
        assert response["mode"] == "off", response

    @vcr.use_cassette('tests/cassettes/TestControlInterface.test_mode_on.yaml')
    def test_mode_on(self):
        control_interface = xled.control.ControlInterface("192.168.1.171")
        control_interface.set_mode("movie")
        response = control_interface.get_mode()
        assert "mode" in response
        assert response["mode"] == "movie", response

    @vcr.use_cassette('tests/cassettes/TestControlInterface.test_mode_demo.yaml')
    def test_mode_demo(self):
        control_interface = xled.control.ControlInterface("192.168.1.171")
        control_interface.set_mode("demo")
        response = control_interface.get_mode()
        assert "mode" in response
        assert response["mode"] == "demo", response
