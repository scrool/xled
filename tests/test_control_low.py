#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import unittest
import warnings
import io
import struct

# import time  # Needed during recording

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


def rotate90(coords):
    return [
        {"x": 1.0 - 2 * ele["y"], "y": (ele["x"] + 1.0) / 2, "z": ele["z"]}
        for ele in coords
    ]


class TestControlInterface(unittest.TestCase):
    """
    Tests for all the methods of ControlInterface in the `xled.control` module,
    except the realtime protocols which are tested separately.
    """

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_misc_info.yaml")
    def test_misc_info(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.check_status()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.led_reset()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.firmware_version()._data
        self.assertEqual(res, {"version": "2.7.1", "code": 1000})
        # print(res)

        res = ctr.get_device_info()._data
        self.assertEqual(
            res,
            {
                "product_name": "Twinkly",
                "hardware_version": "100",
                "bytes_per_led": 3,
                "hw_id": "d64f58",
                "flash_size": 64,
                "led_type": 14,
                "product_code": "TWS250STP-B",
                "fw_family": "F",
                "device_name": "Twinkly_D64F59",
                "uptime": "1058345",
                "mac": "84:0d:8e:d6:4f:59",
                "uuid": "330467ED-C463-4F4E-9FBB-AA0ECE825ADD",
                "max_supported_led": 500,
                "number_of_led": 250,
                "led_profile": "RGB",
                "frame_rate": 20,
                "measured_frame_rate": 23.81,
                "movie_capacity": 992,
                "copyright": "LEDWORKS 2021",
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.get_device_name()._data
        self.assertEqual(res, {"name": "Twinkly_D64F59", "code": 1000})
        # print(res)

        res = ctr.set_device_name(res["name"])._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_led_config()._data
        self.assertEqual(
            res,
            {
                "strings": [
                    {"first_led_id": 0, "length": 125},
                    {"first_led_id": 125, "length": 125},
                ],
                "code": 1000,
            },
        )
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_timer.yaml")
    def test_timer(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.set_timer(3600, 7200)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_timer()._data
        self.assertEqual(
            res, {"time_now": 68181, "time_on": 3600, "time_off": 7200, "code": 1000}
        )
        # print(res)

        res = ctr.set_timer(-1, -1)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

    # Available from fw version 2.4.2
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_mqtt.yaml")
    def test_mqtt(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.get_mqtt_config()._data
        self.assertEqual(
            res,
            {
                "broker_host": "127.0.0.1",
                "broker_port": 8883,
                "client_id": "840D8ED64F59",
                "user": "twinkly32",
                "keep_alive_interval": 7200,
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_mqtt_config(
            res["broker_host"],
            res["broker_port"],
            res["client_id"],
            res["user"],
            res["keep_alive_interval"],
        )._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_effect.yaml")
    def test_effect(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.set_mode("effect")._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_mode()._data
        self.assertEqual(res, {"mode": "effect", "shop_mode": 0, "code": 1000})
        # print(res)

        res = ctr.get_led_effects()._data
        self.assertEqual(
            res,
            {
                "code": 1000,
                "effects_number": 15,
                "unique_ids": [
                    "00000000-0000-0000-0000-000000000001",
                    "00000000-0000-0000-0000-000000000002",
                    "00000000-0000-0000-0000-000000000003",
                    "00000000-0000-0000-0000-000000000004",
                    "00000000-0000-0000-0000-000000000005",
                    "00000000-0000-0000-0000-000000000006",
                    "00000000-0000-0000-0000-000000000007",
                    "00000000-0000-0000-0000-000000000008",
                    "00000000-0000-0000-0000-000000000009",
                    "00000000-0000-0000-0000-00000000000A",
                    "00000000-0000-0000-0000-00000000000B",
                    "00000000-0000-0000-0000-00000000000C",
                    "00000000-0000-0000-0000-00000000000D",
                    "00000000-0000-0000-0000-00000000000E",
                    "00000000-0000-0000-0000-00000000000F",
                ],
            },
        )
        # print(res)

        res = ctr.set_led_effects_current(2)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_led_effects_current()._data
        self.assertEqual(
            res,
            {
                "preset_id": 2,
                "unique_id": "00000000-0000-0000-0000-000000000003",
                "code": 1000,
            },
        )
        # print(res)

    # Available from fw version 2.4.2
    @vcr.use_cassette(
        "tests/cassettes/TestControlInterface.test_brightness_saturation.yaml"
    )
    def test_brightness_saturation(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.set_brightness(50)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.set_brightness(-20, relative=True)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.set_brightness(100, enabled=False)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_brightness()._data
        self.assertEqual(res, {"value": 100, "mode": "disabled", "code": 1000})
        # print(res)

        res = ctr.set_saturation(90)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.set_saturation(-30, relative=True)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.set_saturation(+80, enabled=False, relative=True)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_saturation()._data
        self.assertEqual(res, {"value": 100, "mode": "disabled", "code": 1000})
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_movie_oldif.yaml")
    def test_movie_oldif(self):
        ctr = ControlInterface("192.168.10.100")
        numleds = 250
        m_white = make_solid_movie(numleds, 230, 255, 160)

        res = ctr.get_led_movie_config()._data
        self.assertEqual(
            res,
            {
                "frame_delay": 50,
                "leds_number": 250,
                "loop_type": 0,
                "frames_number": 120,
                "sync": {"mode": "none", "compat_mode": 0},
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_led_movie_full(m_white)._data
        self.assertEqual(res, {"frames_number": 1, "code": 1000})
        # print(res)

        res = ctr.set_led_movie_config(1000, 1, numleds)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.set_mode("movie")._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_mode()._data
        self.assertEqual(
            res,
            {
                "mode": "movie",
                "shop_mode": 0,
                "id": 0,
                "unique_id": "A151A936-2836-4BB2-926C-BE592052D60E",
                "name": "",
                "code": 1000,
            },
        )
        # print(res)

    # Avalable from fw version 2.5.6
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_movie_newif.yaml")
    def test_movie_newif(self):
        ctr = ControlInterface("192.168.10.100")
        numleds = 250
        m_green = make_solid_movie(numleds, 0, 255, 0)
        m_lime = make_solid_movie(numleds, 100, 255, 0)

        ctr.set_mode("off")  # Needed during recording, should not be in movie mode

        res = ctr.delete_movies()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_movies()._data
        self.assertEqual(
            res,
            {"movies": [], "available_frames": 992, "max_capacity": 992, "code": 1000},
        )
        # print(res)

        res = ctr.set_movies_new(
            "green", "00000000-0000-0000-000A-000000000001", "rgb_raw", numleds, 1, 1
        )._data
        self.assertEqual(
            res,
            {
                "entry_point": 0,
                "id": 0,
                "handle": 15,
                "unique_id": "00000000-0000-0000-000A-000000000001",
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_movies_full(m_green)._data
        self.assertEqual(res, {"frames_number": 1, "code": 1000})
        # print(res)

        res = ctr.set_movies_new(
            "lime", "00000000-0000-0000-000A-000000000002", "rgb_raw", numleds, 1, 1
        )._data
        self.assertEqual(
            res,
            {
                "entry_point": 2,
                "id": 1,
                "handle": 16,
                "unique_id": "00000000-0000-0000-000A-000000000002",
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_movies_full(m_lime)._data
        self.assertEqual(res, {"frames_number": 1, "code": 1000})
        # print(res)

        res = ctr.get_movies_current()._data
        self.assertEqual(
            res,
            {
                "id": 1,
                "unique_id": "00000000-0000-0000-000A-000000000002",
                "name": "lime",
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_movies_current(0)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

    # Avalable from fw version 2.5.6
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_playlist.yaml")
    def test_playlist(self):
        ctr = ControlInterface("192.168.10.100")

        # Assumes being recorded after test_movies_newif, so there are some movies
        lst = ctr.get_movies()["movies"]
        pl = [{"unique_id": ele["unique_id"], "duration": 5} for ele in lst]

        res = ctr.set_playlist(pl)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_playlist()._data
        self.assertEqual(
            res,
            {
                "unique_id": "00000000-0000-0000-0000-000000000000",
                "name": "",
                "entries": [
                    {
                        "id": 0,
                        "handle": 15,
                        "name": "green",
                        "unique_id": "00000000-0000-0000-000A-000000000001",
                        "duration": 5,
                    },
                    {
                        "id": 1,
                        "handle": 16,
                        "name": "lime",
                        "unique_id": "00000000-0000-0000-000A-000000000002",
                        "duration": 5,
                    },
                ],
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_mode("playlist")._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_mode()._data
        self.assertEqual(
            res,
            {
                "mode": "playlist",
                "shop_mode": 0,
                "movie": {
                    "id": 0,
                    "unique_id": "00000000-0000-0000-000A-000000000001",
                    "name": "green",
                    "duration": 5,
                },
                "name": "",
                "unique_id": "00000000-0000-0000-0000-000000000000",
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.get_playlist_current()._data
        self.assertEqual(
            res,
            {
                "duration": 5,
                "id": 0,
                "unique_id": "00000000-0000-0000-000A-000000000001",
                "name": "green",
                "code": 1000,
            },
        )
        # print(res)

        res = ctr.set_playlist_current(1)._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.delete_playlist()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_layout.yaml")
    def test_layout(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.get_led_layout()._data
        # res['coordinates'] is very long, skip comparison
        self.assertEqual(res["source"], "2d")
        self.assertEqual(res["synthesized"], False)
        self.assertEqual(res["code"], 1000)
        # print(res)

        res = ctr.set_led_layout(
            res["source"], res["coordinates"], res["synthesized"]
        )._data
        self.assertEqual(res, {"parsed_coordinates": 250, "code": 1000})
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_network_scan.yaml")
    def test_network_scan(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.network_scan()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        # time.sleep(5)  # Needed during recording
        res = ctr.network_scan_results()._data
        self.assertEqual(
            res,
            {
                "code": 1000,
                "networks": [
                    {
                        "ssid": "TN_24GHz_D21CEF",
                        "mac": "30:91:8f:d2:1c:ef",
                        "rssi": 203,
                        "channel": 11,
                        "enc": 4,
                    }
                ],
            },
        )
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_network_mode_ap.yaml")
    def test_network_mode_ap(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.get_network_status()._data
        self.assertEqual(
            res,
            {
                "mode": 1,
                "station": {
                    "ssid": "TN_24GHz_D21CEF",
                    "ip": "192.168.10.100",
                    "gw": "192.168.10.1",
                    "mask": "255.255.255.0",
                    "rssi": -60,
                },
                "ap": {
                    "ssid": "Twinkly_D64F59",
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
        # print(res)

        res = ctr.set_network_mode_ap()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

    @vcr.use_cassette(
        "tests/cassettes/TestControlInterface.test_network_mode_station.yaml"
    )
    def test_network_mode_station(self):
        ctr = ControlInterface("192.168.4.1")

        res = ctr.get_network_status()._data
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
                    "ssid": "Twinkly_D64F59",
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
        # print(res)

        res = ctr.set_network_mode_station()._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_off.yaml")
    def test_off(self):
        ctr = ControlInterface("192.168.10.100")

        res = ctr.set_mode("off")._data
        self.assertEqual(res, {"code": 1000})
        # print(res)

        res = ctr.get_mode()._data
        self.assertEqual(res, {"mode": "off", "shop_mode": 0, "code": 1000})
        # print(res)
