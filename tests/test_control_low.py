#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import unittest
import warnings
import io
import struct
import time

from xled.compat import is_py2
from xled.control import ControlInterface


with warnings.catch_warnings():
    if is_py2:
        warnings.simplefilter("ignore", category=DeprecationWarning)
    import vcr


def make_solid_movie(num, nbytes, r, g, b):
    if nbytes == 4:
        pat = [struct.pack(">BBBB", 0, r, g, b)] * num
    else:
        pat = [struct.pack(">BBB", r, g, b)] * num
    movie = io.BytesIO()
    movie.write(b"".join(pat))
    movie.seek(0)
    return movie


class TestControlInterface(unittest.TestCase):
    """
    Tests for all the methods of ControlInterface in the `xled.control` module,
    except the realtime protocols and the network modes, which are tested separately.
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

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_misc_calls.yaml")
    def test_misc_calls(self):
        ctr = ControlInterface(self.host)

        res = ctr.check_status()._data
        if self.isrecording:
            print("check_status:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.led_reset()._data
        if self.isrecording:
            print("led_reset:", res)
        else:
            self.assertEqual(res, {"code": 1000})

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_misc_info.yaml")
    def test_misc_info(self):
        ctr = ControlInterface(self.host)

        res = ctr.firmware_version()._data
        if self.isrecording:
            print("firmware_version:", res)
        else:
            self.assertEqual(res, {"version": "2.7.1", "code": 1000})

        res = ctr.get_device_info()._data
        if self.isrecording:
            print("get_device_info:", res)
        else:
            self.assertEqualSubdict(
                res,
                {
                    "product_name": "Twinkly",
                    "hardware_version": "100",
                    "bytes_per_led": 3,
                    "hw_id": "abcdee",
                    "flash_size": 64,
                    "led_type": 14,
                    "product_code": "TWS250STP-B",
                    "fw_family": "F",
                    "device_name": "Twinkly_ABCDEF",
                    "mac": "01:23:45:67:89:ab",
                    "uuid": "00000000-0000-0000-0000-000000000000",
                    "max_supported_led": 500,
                    "number_of_led": 250,
                    "led_profile": "RGB",
                    "frame_rate": 20,
                    "movie_capacity": 992,
                    "copyright": "LEDWORKS 2021",
                    "code": 1000,
                },
            )

        res = ctr.get_led_config()._data
        if self.isrecording:
            print("get_led_config:", res)
        else:
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

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_name.yaml")
    def test_name(self):
        ctr = ControlInterface(self.host)

        # Do not clobber old name during recording
        oldname = ctr.get_device_name()._data

        res = ctr.set_device_name("Cucumber")._data
        if self.isrecording:
            print("set_device_name:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_device_name()._data
        if self.isrecording:
            print("get_device_name:", res)
        else:
            self.assertEqual(res, {"name": "Cucumber", "code": 1000})

        ctr.set_device_name(oldname["name"])

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_timer.yaml")
    def test_timer(self):
        ctr = ControlInterface(self.host)

        res = ctr.set_timer(3600, 7200)._data
        if self.isrecording:
            print("set_timer 1:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_timer()._data
        if self.isrecording:
            print("get_timer:", res)
        else:
            self.assertEqualSubdict(
                res, {"time_on": 3600, "time_off": 7200, "code": 1000}
            )

        res = ctr.set_timer(-1, -1)._data
        if self.isrecording:
            print("set_timer 2:", res)
        else:
            self.assertEqual(res, {"code": 1000})

    # Available from fw version 2.4.2
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_mqtt.yaml")
    def test_mqtt(self):
        ctr = ControlInterface(self.host)

        # Do not clobber old mqtt config during recording
        oldmqtt = ctr.get_mqtt_config()._data

        res = ctr.set_mqtt_config(
            "127.0.0.1",
            8883,
            "ABCDEF123456",
            "Bigfoot99",
            7200,
        )._data
        if self.isrecording:
            print("set_mqtt_config:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_mqtt_config()._data
        if self.isrecording:
            print("get_mqtt_config:", res)
        else:
            self.assertEqualSubdict(
                res,
                {
                    "broker_host": "127.0.0.1",
                    "broker_port": 8883,
                    "client_id": "ABCDEF123456",
                    "user": "Bigfoot99",
                    "keep_alive_interval": 7200,
                    "code": 1000,
                },
            )

        ctr.set_mqtt_config(
            oldmqtt["broker_host"],
            oldmqtt["broker_port"],
            oldmqtt["client_id"],
            oldmqtt["user"],
            oldmqtt["keep_alive_interval"],
        )

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_effect.yaml")
    def test_effect(self):
        ctr = ControlInterface(self.host)

        res = ctr.set_mode("effect")._data
        if self.isrecording:
            print("set_mode:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_mode()._data
        if self.isrecording:
            print("get_mode:", res)
        else:
            self.assertEqual(res, {"mode": "effect", "shop_mode": 0, "code": 1000})

        res = ctr.get_led_effects()._data
        if self.isrecording:
            print("get_led_effects:", res)
        else:
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

        res = ctr.set_led_effects_current(2)._data
        if self.isrecording:
            print("set_led_effects_current:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_led_effects_current()._data
        if self.isrecording:
            print("get_led_effects_current:", res)
        else:
            self.assertEqual(
                res,
                {
                    "preset_id": 2,
                    "unique_id": "00000000-0000-0000-0000-000000000003",
                    "code": 1000,
                },
            )

    # Available from fw version 2.4.2
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_brightness.yaml")
    def test_brightness(self):
        ctr = ControlInterface(self.host)

        res = ctr.set_brightness(50)._data
        if self.isrecording:
            print("set_brightness 1:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.set_brightness(-20, relative=True)._data
        if self.isrecording:
            print("set_brightness 2:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.set_brightness(100, enabled=False)._data
        if self.isrecording:
            print("set_brightness 3:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_brightness()._data
        if self.isrecording:
            print("get_brightness:", res)
        else:
            self.assertEqual(res, {"value": 100, "mode": "disabled", "code": 1000})

    # Available from fw version 2.4.2
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_saturation.yaml")
    def test_saturation(self):
        ctr = ControlInterface(self.host)

        res = ctr.set_saturation(90)._data
        if self.isrecording:
            print("set_saturation 1:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.set_saturation(-30, relative=True)._data
        if self.isrecording:
            print("set_saturation 2:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.set_saturation(+80, enabled=False, relative=True)._data
        if self.isrecording:
            print("set_saturation 3:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_saturation()._data
        if self.isrecording:
            print("get_saturation:", res)
        else:
            self.assertEqual(res, {"value": 100, "mode": "disabled", "code": 1000})

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_movie_oldif.yaml")
    def test_movie_1_oldif(self):
        ctr = ControlInterface(self.host)
        m_white = make_solid_movie(self.numleds, self.ledbytes, 230, 255, 160)

        res = ctr.set_led_movie_full(m_white)._data
        if self.isrecording:
            print("set_led_movie_full:", res)
        else:
            self.assertEqual(res, {"frames_number": 1, "code": 1000})

        res = ctr.set_led_movie_config(1000, 1, self.numleds)._data
        if self.isrecording:
            print("set_led_movie_config:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_led_movie_config()._data
        if self.isrecording:
            print("get_led_movie_config:", res)
        else:
            self.assertEqual(
                res,
                {
                    "frame_delay": 1000,
                    "leds_number": self.numleds,
                    "loop_type": 0,
                    "frames_number": 1,
                    "sync": {"mode": "none", "compat_mode": 0},
                    "code": 1000,
                },
            )

        res = ctr.set_mode("movie")._data
        if self.isrecording:
            print("set_mode:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_mode()._data
        if self.isrecording:
            print("get_mode:", res)
        else:
            self.assertEqualSubdict(
                res,
                {
                    "mode": "movie",
                    "shop_mode": 0,
                    "id": 0,
                    "code": 1000,
                },
            )

    # Avalable from fw version 2.5.6
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_movie_newif.yaml")
    def test_movie_2_newif(self):
        ctr = ControlInterface(self.host)
        m_green = make_solid_movie(self.numleds, self.ledbytes, 0, 255, 0)
        m_lime = make_solid_movie(self.numleds, self.ledbytes, 100, 255, 0)

        # Needed during recording, device should not be in movie mode
        ctr.set_mode("off")

        res = ctr.delete_movies()._data
        if self.isrecording:
            print("delete_movies:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_movies()._data
        if self.isrecording:
            print("get_movies:", res)
        else:
            self.assertEqual(
                res,
                {
                    "movies": [],
                    "available_frames": 992,
                    "max_capacity": 992,
                    "code": 1000,
                },
            )

        res = ctr.set_movies_new(
            "green",
            "00000000-0000-0000-000A-000000000001",
            "rgb_raw" if self.ledbytes == 3 else "rgbw_raw",
            self.numleds,
            1,
            1,
        )._data
        if self.isrecording:
            print("set_movies_new 1:", res)
        else:
            self.assertEqualSubdict(
                res,
                {
                    "entry_point": 0,
                    "id": 0,
                    "unique_id": "00000000-0000-0000-000A-000000000001",
                    "code": 1000,
                },
            )

        res = ctr.set_movies_full(m_green)._data
        if self.isrecording:
            print("set_movies_full 1:", res)
        else:
            self.assertEqual(res, {"frames_number": 1, "code": 1000})

        res = ctr.set_movies_new(
            "lime",
            "00000000-0000-0000-000A-000000000002",
            "rgb_raw" if self.ledbytes == 3 else "rgbw_raw",
            self.numleds,
            1,
            1,
        )._data
        if self.isrecording:
            print("set_movies_new 2:", res)
        else:
            self.assertEqualSubdict(
                res,
                {
                    "entry_point": 2,
                    "id": 1,
                    "unique_id": "00000000-0000-0000-000A-000000000002",
                    "code": 1000,
                },
            )

        res = ctr.set_movies_full(m_lime)._data
        if self.isrecording:
            print("set_movies_full 2:", res)
        else:
            self.assertEqual(res, {"frames_number": 1, "code": 1000})

        res = ctr.set_movies_current(0)._data
        if self.isrecording:
            print("set_movies_current:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_movies_current()._data
        if self.isrecording:
            print("get_movies_current:", res)
        else:
            self.assertEqual(
                res,
                {
                    "id": 0,
                    "unique_id": "00000000-0000-0000-000A-000000000001",
                    "name": "green",
                    "code": 1000,
                },
            )

    # Avalable from fw version 2.5.6
    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_playlist.yaml")
    def test_movie_3_playlist(self):
        ctr = ControlInterface(self.host)

        # Assumes being recorded after test_movies_newif, so there are some movies
        lst = ctr.get_movies()["movies"]
        pl = [{"unique_id": ele["unique_id"], "duration": 5} for ele in lst]

        res = ctr.set_playlist(pl)._data
        if self.isrecording:
            print("set_playlist:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_playlist()._data
        if self.isrecording:
            print("get_playlist:", res)
        else:
            self.assertEqualSubdict(
                res,
                {
                    "unique_id": "00000000-0000-0000-0000-000000000000",
                    "name": "",
                    "code": 1000,
                },
            )
            self.assertIn("entries", res)
            self.assertEqual(len(res["entries"]), 2)
            self.assertEqualSubdict(
                res["entries"][0],
                {
                    "id": 0,
                    "name": "green",
                    "unique_id": "00000000-0000-0000-000A-000000000001",
                    "duration": 5,
                },
            )
            self.assertEqualSubdict(
                res["entries"][1],
                {
                    "id": 1,
                    "name": "lime",
                    "unique_id": "00000000-0000-0000-000A-000000000002",
                    "duration": 5,
                },
            )

        res = ctr.set_mode("playlist")._data
        if self.isrecording:
            print("set_mode:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_mode()._data
        if self.isrecording:
            print("get_mode:", res)
        else:
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

        res = ctr.set_playlist_current(1)._data
        if self.isrecording:
            print("set_playlist_current:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_playlist_current()._data
        if self.isrecording:
            print("get_playlist_current:", res)
        else:
            self.assertEqual(
                res,
                {
                    "duration": 5,
                    "id": 1,
                    "unique_id": "00000000-0000-0000-000A-000000000002",
                    "name": "lime",
                    "code": 1000,
                },
            )

        res = ctr.delete_playlist()._data
        if self.isrecording:
            print("delete_playlist:", res)
        else:
            self.assertEqual(res, {"code": 1000})

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_layout.yaml")
    def test_layout(self):
        ctr = ControlInterface(self.host)

        res = ctr.get_led_layout()._data
        if self.isrecording:
            print("get_led_layout:", res)
        else:
            # res['coordinates'] is very long, skip comparison
            self.assertIn(res["source"], ["2d", "3d", "linear"])
            self.assertIn(res["synthesized"], [False, True])
            self.assertEqual(res["code"], 1000)

        res = ctr.set_led_layout(
            res["source"], res["coordinates"], res["synthesized"]
        )._data
        if self.isrecording:
            print("set_led_layout:", res)
        else:
            self.assertEqual(res, {"parsed_coordinates": self.numleds, "code": 1000})

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_network_scan.yaml")
    def test_network_scan(self):
        ctr = ControlInterface(self.host)

        res = ctr.network_scan()._data
        if self.isrecording:
            print("network_scan:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        if self.isrecording:
            time.sleep(5)  # Needed during recording

        res = ctr.network_scan_results()._data
        if self.isrecording:
            print("network_scan_results:", res)
        else:
            self.assertEqual(
                res,
                {
                    "code": 1000,
                    "networks": [
                        {
                            "ssid": "MyWiFi",
                            "mac": "00:11:22:33:44:55",
                            "rssi": 208,
                            "channel": 6,
                            "enc": 4,
                        }
                    ],
                },
            )

    @vcr.use_cassette("tests/cassettes/TestControlInterface.test_modes.yaml")
    def test_modes(self):
        ctr = ControlInterface(self.host)

        res = ctr.set_mode("demo")._data
        if self.isrecording:
            print("set_mode 1:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_mode()._data
        if self.isrecording:
            print("get_mode 1:", res)
        else:
            self.assertEqual(res, {"mode": "demo", "shop_mode": 0, "code": 1000})

        res = ctr.set_mode("off")._data
        if self.isrecording:
            print("set_mode 2:", res)
        else:
            self.assertEqual(res, {"code": 1000})

        res = ctr.get_mode()._data
        if self.isrecording:
            print("get_mode 2:", res)
        else:
            self.assertEqual(res, {"mode": "off", "shop_mode": 0, "code": 1000})
