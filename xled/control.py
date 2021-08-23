# -*- coding: utf-8 -*-

"""
xled.control
~~~~~~~~~~~~~

This module contains interface to control specific device

.. seealso::

    :doc:`xled-docs:rest_api`
        for more details about API that is used by the application.

    :doc:`xled-docs:protocol_details`
        for various operations.
"""

from __future__ import absolute_import

import collections
import io
import logging
import struct
import binascii
from operator import xor

from requests.compat import urljoin

import xled.util
from xled.auth import BaseUrlChallengeResponseAuthSession
from xled.exceptions import HighInterfaceError
from xled.response import ApplicationResponse
from xled.security import encrypt_wifi_password

log = logging.getLogger(__name__)

#: Time format as defined by C standard
TIME_FORMAT = "%H:%M:%S"


class ControlInterface(object):
    """
    Main interface to control specific device

    :param str host: Hostname (or IP address) of a device to control
    """

    def __init__(self, host, hw_address=None):
        self.host = host
        self.hw_address = hw_address
        self._session = None
        self._base_url = None

    @property
    def base_url(self):
        if not self._base_url:
            self._base_url = "http://{}/xled/v1/".format(self.host)
            assert self._base_url
        return self._base_url

    @property
    def session(self):
        """
        Session object to operate on

        :return: session object with auth
            :py:class:`~.auth.BaseUrlChallengeResponseAuthSession()`.
        :rtype: requests.Session
        """
        if not self._session:
            self._session = BaseUrlChallengeResponseAuthSession(
                hw_address=self.hw_address, base_url=self.base_url
            )
            assert self._session
        return self._session

    def check_status(self):
        """
        Check that the device is online and responding

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "status")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def firmware_0_update(self, firmware):
        """
        Uploads first stage of the firmware

        :param firmware: file-like object that points to firmware file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "fw/0/update")
        response = self.session.post(url, data=firmware)
        app_response = ApplicationResponse(response)
        return app_response

    def firmware_1_update(self, firmware):
        """
        Uploads second stage of the firmware

        :param firmware: file-like object that points to firmware file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "fw/1/update")
        response = self.session.post(url, data=firmware)
        app_response = ApplicationResponse(response)
        return app_response

    def firmware_update(self, stage0_sha1sum, stage1_sha1sum=None):
        """
        Performs firmware update from previously uploaded images

        :param str stage0_sha1sum: SHA1 digest of first stage
        :param str stage1_sha1sum: SHA1 digest of second stage
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        if stage1_sha1sum is not None:
            json_payload = {
                "checksum": {
                    "stage0_sha1sum": stage0_sha1sum,
                    "stage1_sha1sum": stage1_sha1sum,
                }
            }
        else:
            json_payload = {
                "checksum": {
                    "stage0_sha1sum": stage0_sha1sum,
                }
            }
        url = urljoin(self.base_url, "fw/update")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        return app_response

    def firmware_version(self):
        """
        Gets firmware version

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "fw/version")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def get_brightness(self):
        """
        Gets current brightness level and if dimming is applied

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/out/brightness")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code", u"mode", u"value"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_device_info(self):
        """
        Gets detailed information about device

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "gestalt")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def get_device_name(self):
        """
        Gets device name.

        .. seealso:: :py:meth:`set_device_name()`

        :raises ApplicationError: on application error
        :return: current device name.
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "device_name")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code", u"name"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_led_config(self):
        """
        Gets the structural configuration of the leds in term of strings

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/config")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def get_led_current_effect(self):
        """
        Get the current effect index

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/effects/current")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def get_led_movie_config(self):
        """
        Gets the parameters for playing the uploaded movie

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/movie/config")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def get_network_status(self):
        """
        Gets network status

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "network/status")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def get_mode(self):
        """
        Gets current LED operation mode.

        .. seealso:: :py:meth:`set_mode()` to set modes.

        :raises ApplicationError: on application error
        :return: current LED operation mode. See :py:meth:`set_mode()` for
            possible return values.
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/mode")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code", u"mode"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_timer(self):
        """
        Gets current timer

        :type time_now: int or None
        :raises ApplicationError: on application error
        :return: {time_on, time_off, time_now}. See :py:meth:`set_timer()` for
            explanation of return values.
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "timer")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"time_now", u"time_off", u"time_on"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def led_reset(self):
        """
        Resets LED

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/reset")
        response = self.session.get(url)
        return ApplicationResponse(response)

    def network_scan(self):
        """
        Initiate WiFi network scan

        :raises ApplicationError: on application error
        :rtype: None
        """
        url = urljoin(self.base_url, "network/scan")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def network_scan_results(self):
        """
        Get results of WiFi network scan

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "network/scan_results")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        return app_response

    def set_brightness(self, brightness=None, enabled=True):
        """
        Sets new brightness or enable/disable brightness dimming

        :param brightness: new brightness in range of 0..255 or None if no
                           change is requested
        :param bool enabled: set to False if the dimming should not be applied
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        assert brightness in range(0, 256) or brightness is None
        if enabled:
            json_payload = {"mode": "enabled", "type": "A"}
        else:
            json_payload = {"mode": "disabled"}
        if brightness is not None:
            json_payload["value"] = brightness
        url = urljoin(self.base_url, "led/out/brightness")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_device_name(self, name):
        """
        Sets new device name

        :param str name: new device name
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert len(name) <= 32
        json_payload = {"name": name}
        url = urljoin(self.base_url, "device_name")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def set_led_current_effect(self, id):
        """
        Sets the current effect of effect mode

        :param int id: Effect id
        :raises ApplicationError: on application error
        :rtype: None
        """
        json_payload = {"effect_id": id}
        url = urljoin(self.base_url, "led/effects/current")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def set_led_movie_config(self, frame_delay, frames_number, leds_number):
        """
        Sets movie configuration for the last uploaded movie

        :param int frame_delay: speed of movie (delay between frames in ms)
        :param int leds_number: total number of LEDs
        :param int frames_number: total number of frames
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {
            "frame_delay": frame_delay,
            "frames_number": frames_number,
            "leds_number": leds_number,
        }
        url = urljoin(self.base_url, "led/movie/config")
        response = self.session.post(url, json=json_payload)
        return ApplicationResponse(response)

    def set_led_movie_full(self, movie):
        """
        Uploads movie

        :param movie: file-like object that points to movie file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/movie/full")
        head = {"Content-Type": "application/octet-stream"}
        response = self.session.post(url, headers=head, data=movie)
        return ApplicationResponse(response)

    def set_mode(self, mode):
        """
        Sets new LED operation mode.

        :param str mode: Mode to set. One of 'movie', 'demo', 'effect' or 'off'.
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert mode in ("movie", "demo", "effect", "off")
        json_payload = {"mode": mode}
        url = urljoin(self.base_url, "led/mode")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def set_network_mode_ap(self):
        """
        Sets network mode to Access Point

        :raises ApplicationError: on application error
        :rtype: None
        """
        json_payload = {"mode": 2}
        url = urljoin(self.base_url, "network/status")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def set_network_mode_station(self, ssid, password):
        """
        Sets network mode to Station

        :param str ssid: SSID if the access point to connect to
        :param str password: password to use
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert self.hw_address
        encpassword = encrypt_wifi_password(password, self.hw_address)
        json_payload = {
            "mode": 1,
            "station": {"dhcp": 1, "ssid": ssid, "encpassword": encpassword},
        }
        url = urljoin(self.base_url, "network/status")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def set_timer(self, time_on, time_off, time_now=None):
        """
        Sets new timer

        :param int time_on: time when to turn lights on. In seconds after
            midnight. To disable use -1.
        :param int time_off: time when to turn lights off. In seconds after
            midnight. To disable use -1.
        :param time_now: current time in seconds after midnight. Determined
            automatically if not set.
        :type time_now: int or None
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert isinstance(time_on, int)
        assert time_on >= -1
        assert isinstance(time_off, int)
        assert time_off >= -1
        if time_now is None:
            time_now = xled.util.seconds_after_midnight()
            log.debug("Setting time now to %s", time_now)

        json_payload = {"time_on": time_on, "time_off": time_off, "time_now": time_now}
        url = urljoin(self.base_url, "timer")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)


class HighControlInterface(ControlInterface):
    """
    High level interface to control specific device
    """

    def __init__(self, host, hw_address=None):
        super(HighControlInterface, self).__init__(host, hw_address)
        info = self.get_device_info()
        self.num_leds = info['number_of_led']
        self.family = info['fw_family'] if 'fw_family' in info else "D"
        self.led_bytes = info['bytes_per_led'] if 'bytes_per_led' in info else 3
        self.string_config = self.get_led_config()['strings']
        self.last_mode = None
        self.curr_mode = self.get_mode()['mode']

    def update_firmware(self, stage0, stage1=None):
        """
        Uploads firmware and runs update

        :param stage0: file-like seekable object pointing to stage0 of firmware.
        optional :param stage1: file-like seekable object pointing to stage1 of firmware.
        :raises ApplicationError: on application error
        :raises HighInterfaceError: on error during update
        """
        fw_stage_sums = [None, None]
        fw_images = [stage0, stage1]
        fw_funcalls = [self.firmware_0_update, self.firmware_1_update]
        stages = [0, 1] if stage1 is not None else [0]
        for stage in stages:
            if stage1 is None:
                continue
            # I don't know how to dynamically construct variable name
            # Something like this you mean? / aho
            fw_images[stage].seek(0)
            fw_stage_sums[stage] = xled.security.sha1sum(fw_images[stage])
            log.debug("Firmware stage %d SHA1SUM: %r", stage, fw_stage_sums[stage])
            if not fw_stage_sums[stage]:
                msg = "Failed to compute SHA1SUM for firmware stage {}.".format(stage)
                raise HighInterfaceError(msg)
                assert False

        uploaded_stage_sums = [None, None]
        for stage in stages:
            log.debug("Uploading firmware stage %d...", stage)
            fw_images[stage].seek(0)
            response = fw_funcalls[stage](fw_images[stage])
            log.debug("Firmware stage %d uploaded.", stage)
            if not response.ok:
                msg = "Failed to upload stage {}: {}".format(
                    stage, response.status_code
                )
                raise HighInterfaceError(msg)
                assert False

            uploaded_stage_sums[stage] = response.get("sha1sum")
            log.debug(
                "Uploaded stage %d SHA1SUM: %r", stage, uploaded_stage_sums[stage]
            )
            if not uploaded_stage_sums[stage]:
                msg = "Device didn't return SHA1SUM for stage {}.".format(stage)
                raise HighInterfaceError(msg)
                assert False

        if fw_stage_sums != uploaded_stage_sums:
            log.error("Firmware SHA1SUMs: %r != uploaded SHA1SUMs", fw_stage_sums)
            msg = "Firmware SHA1SUMs doesn't match uploaded SHA1SUMs."
            raise HighInterfaceError(msg)
            assert False
        else:
            log.debug("Firmware SHA1SUMs matches.")

        response = self.firmware_update(fw_stage_sums[0], fw_stage_sums[1])
        if not response.ok:
            msg = "Failed to update firmware: {}.".format(response.status_code)
            raise HighInterfaceError(msg)
            assert False

    def disable_timer(self):
        """
        Disables timer
        """
        return self.set_timer(-1, -1)

    def get_formatted_timer(self):
        """
        Gets current time and timer

        :return: namedtuple of formatted entries: current time, turn on time,
            turn off time.
        :rtype: namedtuple
        """
        Timer = collections.namedtuple("Timer", ["now", "on", "off"])

        device_response = self.get_timer()

        if xor(device_response["time_on"] == -1, device_response["time_off"] == -1):
            msg = "Inconsistent timer configuration. On: {timer_on}, off: {timer_off}".format(
                **device_response
            )
            raise HighInterfaceError(msg)

        now = device_response["time_now"]
        now_formatted = xled.util.date_from_seconds_after_midnight(now).strftime(
            TIME_FORMAT
        )

        if device_response["time_on"] == -1 and device_response["time_off"] == -1:
            return Timer(now_formatted, False, False)

        on = device_response["time_on"]
        on_formatted = xled.util.date_from_seconds_after_midnight(on).strftime(
            TIME_FORMAT
        )

        off = device_response["time_off"]
        off_formatted = xled.util.date_from_seconds_after_midnight(off).strftime(
            TIME_FORMAT
        )

        return Timer(now_formatted, on_formatted, off_formatted)

    def set_formatted_timer(self, timestr_on, timestr_off):
        """
        Sets timer on and off times, given as strings in H:M:S format

        """
        time_on = xled.util.seconds_after_midnight_from_string(timestr_on, TIME_FORMAT)
        time_off = xled.util.seconds_after_midnight_from_string(timestr_off, TIME_FORMAT)

        return self.set_timer(time_on, time_off)

    def turn_on(self):
        """
        Turns on the device.
        """
        if self.last_mode:
            return self.set_mode(self.last_mode)
        else:
            resp = self.get_led_movie_config()
            self.set_mode("effect" if resp['frames_number'] == 0 else "movie")

    def turn_off(self):
        """
        Turns off the device.
        """
        mode = self.get_mode()["mode"]
        if mode != "off":
            self.last_mode = mode
        return self.set_mode("off")

    def is_on(self):
        """
        Returns True if device is on
        """
        return self.get_mode()["mode"] != "off"

    def set_mode(self, mode):
        if mode in ("movie", "demo", "effect", "off"):  # Wait with "rt" until supported
            self.curr_mode = mode
            if mode != "off":
                self.last_mode = mode
            super(HighControlInterface, self).set_mode(mode)

    # Functions for creating and manipulating movies and patterns (single frames of movies)

    def show_movie(self, movie, delay):
        """
        Uploads a movie and starts playing it with the provided frame delay.
        Switches to movie mode if necessary.
        The movie is an object suitable created with to_movie or make_func_movie.

        :param movie: file-like object that points to movie
        :param float delay: frame delay in milliseconds
        """
        numframes = movie.seek(0, 2) // (self.led_bytes * self.num_leds)
        movie.seek(0)
        self.set_led_movie_config(delay, numframes, self.num_leds)
        self.set_led_movie_full(movie)
        if (self.curr_mode != 'movie'):
            self.set_mode('movie')

    def show_pattern(self, pat):
        """
        Uploads a single pattern as a static movie, and shows it.
        Switches to movie mode if necessary.
        The movie is a pattern object eg created with make_solid_pattern or make_func_pattern.

        :param pat: list of byte strings representing a single frame pattern
        """
        self.set_led_movie_config(1, 1, self.num_leds)
        self.set_led_movie_full(self.to_movie(pat))
        if (self.curr_mode != 'movie'):
            self.set_mode('movie')

    def show_demo(self, id):
        """
        Shows the demo with the provided id.
        Switches to demo mode if necessary.

        :param int id: The demo id to show
        """
        self.set_led_current_effect(id)
        if (self.curr_mode != 'demo'):
            self.set_mode('demo')

    def make_func_movie(self, numframes, func):
        """
        Creates a movie of a number of frames by calling a function to create each frame.
        The function is expected to take the frame index as argument and to return a
        pattern object representing the frame.

        :param int numframes: The number of frames for the movie
        :param function func: A function to produce each frame
        :rtype: _io.BytesIO
        """
        pl = []
        for i in range(numframes):
            pl.append(func(i))
        return self.to_movie(pl)

    def make_empty_movie(self):
        """
        Creates a movie of zero frames.
        Meant to be followed by several calls to add_to_movie to add frames to it.

        :rtype: _io.BytesIO
        """
        movie = io.BytesIO()
        return movie

    def is_pattern(self, pat):
        """
        Checks whether the given argument has the format of a single frame pattern.

        :param pat: object to check whether it is a pattern
        :rtype: bool
        """
        return isinstance(pat, list) and len(pat) == self.num_leds and isinstance(pat[0], bytes)

    def add_to_movie(self, movie, pat):
        """
        Adds one pattern as a frame to the end of a movie.

        :param movie: file-like object representing the movie
        :param pat: object representing the pattern
        :rtype: _io.BytesIO
        """
        assert self.is_pattern(pat)
        movie.seek(0, 2)
        movie.write(b''.join(pat))
        movie.seek(0, 0)

    def to_movie(self, patlst):
        """
        Creates a movie from either a single pattern or a list of patterns.

        :param patlst: pattern or list of patterns
        :rtype: _io.BytesIO
        """
        movie = io.BytesIO()
        if isinstance(patlst, list):
            for ele in patlst:
                if isinstance(ele, list):
                    ele = b''.join(ele)
                movie.write(ele)
        else:
            movie.write(patlst)
        movie.seek(0)
        return movie

    def circind(self, ind):
        """
        Internal function used to fascilitate linear or circular effects. That
        is, if the device consists of two strings, flip the led indices of one
        of the strings so they start at the extreme end of the first string
        and runs into the middle where the strings meet and then continue out
        on the other string. If the extreme ends of the two strings are
        arranged to meet again, it allows for circular patterns.
        """
        if len(self.string_config) == 2 and ind < self.string_config[0]['length']:
            return self.string_config[0]['length'] - 1 - ind
        else:
            return ind

    def make_pixel(self, r, g, b):
        """
        Internal function to produce one pixel of a pattern from given r, g
        and b values. Handles both RGB and RGBW led profiles (for now always
        setting the white led to zero).

        :param int r: red component
        :param int g: green component
        :param int b: blue component
        :rtype: bytes
        """
        if self.led_bytes == 4:
            return struct.pack(">BBBB", 0, r, g, b)
        else:
            return struct.pack(">BBB", r, g, b)

    def make_solid_pattern(self, rgb):
        """
        Creates a one-colored pattern with the given rgb value tuple.

        :param tuple rgb: color as an rgb tuple
        :rtype: list representing the pattern
        """
        pat = [self.make_pixel(*rgb)] * self.num_leds
        return pat

    def make_func_pattern(self, func, circular=False):
        """
        Creates a pattern by calling the given function for each led.
        The function is expected to take the led index as argument and to
        return a color as an rgb tuple for that led.

        :param function func: function to return the color of each pixel
        optional :param bool circular: Flip the led indices on two-string devices to enable circular patterns
        :rtype: list representing the pattern
        """
        pat = [False] * self.num_leds
        for i in range(self.num_leds):
            (r, g, b) = func(i)
            if circular:
                pat[self.circind(i)] = self.make_pixel(r, g, b)
            else:
                pat[i] = self.make_pixel(r, g, b)
        return pat

    def copy_pattern(self, pat):
        """
        Make a copy of a pattern.
        In case you want to make destructive operations on one of them.

        :param pat: object representing the pattern
        :rtype: list representing the pattern
        """
        return [ele for ele in pat]

    def modify_pattern(self, pat, ind, rgb, circular=False):
        """
        Modifies one pixel in a pattern.
        Changes the pattern in place. Make sure to copy it if you need the old one.

        :param pat: object representing the pattern
        :param int ind: led index in the pattern
        :param tuple rgb: color as an rgb tuple
        optional :param bool circular: Flip the led indices on two-string devices to enable circular patterns
        :rtype: list representing the pattern (the same object as pat)
        """
        if circular:
            pat[self.circind(ind)] = self.make_pixel(*rgb)
        else:
            pat[ind] = self.make_pixel(*rgb)
        return pat

    def shift_pattern(self, pat, step, rgb, circular=False):
        """
        Shifts the pattern a number of steps, padding with the provided rgb color.
        Non-destructive, leaving the original pattern unmodified.

        :param pat: object representing the pattern
        :param int step: steps to shift, can be positive or negative
        :param tuple rgb: color as an rgb tuple
        optional :param bool circular: Flip the led indices on two-string devices to enable circular patterns
        :rtype: list representing the pattern
        """
        pix = self.make_pixel(*rgb)
        if circular and len(self.string_config) == 2:
            n1 = self.string_config[0]['length']
            n2 = self.num_leds
            p1 = pat[0:n1]
            p2 = pat[n1:n2]
            if step > 0:
                for i in range(step):
                    p2 = p1[:1] + p2[:-1]
                    p1 = p1[1:] + [pix]
            else:
                for i in range(-step):
                    p1 = p2[:1] + p1[:-1]
                    p2 = p2[1:] + [pix]
            pat = p1 + p2
        else:
            if step > 0:
                pat = [pix] * step + pat[:-step]
            else:
                pat = pat[-step:] + [pix] * -step
        return pat

    def rotate_pattern(self, pat, step, circular=False):
        """
        Shifts the pattern a number of steps with rotation, so that pixels
        shifted out at one end emerges at the other end.
        Non-destructive, leaving the original pattern unmodified.

        :param pat: object representing the pattern
        :param int step: steps to shift, can be positive or negative
        optional :param bool circular: Flip the led indices on two-string devices to enable circular patterns
        :rtype: list representing the pattern
        """
        if circular and len(self.string_config) == 2:
            n1 = self.string_config[0]['length']
            n2 = self.num_leds
            p1 = pat[0:n1]
            p2 = pat[n1:n2]
            if step > 0:
                for i in range(step):
                    tmp = p1[0]
                    p1 = p1[1:] + p2[-1:]
                    p2 = [tmp] + p2[:-1]
            else:
                for i in range(-step):
                    tmp = p1[-1]
                    p1 = p2[:1] + p1[:-1]
                    p2 = p2[1:] + [tmp]
            pat = p1 + p2
        else:
            pat = pat[-step:] + pat[:-step]
        return pat

    def permute_pattern(self, pat, perm, circular=False):
        """
        Permutes the pattern according to the provided permutation list.
        The new index 'i' will get the same color as the old index 'perm[i]'.
        Non-destructive, leaving the original pattern unmodified.

        :param pat: object representing the pattern
        :param list perm: permutation list of source indices
        optional :param bool circular: Flip the led indices on two-string devices to enable circular patterns
        :rtype: list representing the pattern
        """
        newpat = [False] * len(pat)
        if circular:
            for i, k in enumerate(perm):
                newpat[self.circind(i)] = pat[self.circind(k)]
        else:
            for i, k in enumerate(perm):
                newpat[i] = pat[k]
        return newpat

    def save_movie(self, name, movie, delay):
        """
        Save the movie object on file.
        The movie file is text based and starts with a header containing
        the number of frames, number of leds, number of bytes per led, and
        the suggested frame delay. After the header follows one line per
        frame as a hexadecimal string. This format makes it easier to share
        movies between different devices and even different led profiles.
        """
        bytesperframe = self.led_bytes * self.num_leds
        numframes = movie.seek(0, 2) // bytesperframe
        movie.seek(0)
        f = open(name, "w")
        f.write("{} {} {} {}\n".format(numframes, self.num_leds, self.led_bytes, int(delay)))
        for i in range(numframes):
            f.write(binascii.hexlify(movie.read(bytesperframe)).decode() + "\n")
        f.close()

    def load_movie(self, name):
        """
        Read a movie from a file (produced by save_movie).
        Returns both the movie object and the suggested frame delay in a tuple.
        Some effort is made to convert movies between different devices:
        If the number of leds are different, each frame is padded or truncated
        at both ends. If the led profile is different, the white component is
        removed or added (as zero).
       """
        f = open(name, "r")
        head = list(map(int, f.readline().strip("\n").split(" ")))
        numframes = head[0]
        delay = head[3]
        movie = io.BytesIO()
        if head[1] == self.num_leds and head[2] == self.led_bytes:
            for i in range(numframes):
                movie.write(binascii.unhexlify(f.readline().strip("\n")))
        else:
            for i in range(numframes):
                s = binascii.unhexlify(f.readline().strip("\n"))
                if head[2] == 3 and self.led_bytes == 4:
                    s = b''.join([chr(0) + s[3 * i : 3 * i + 3] for i in range(len(s) // 3)])
                elif head[2] == 4 and self.led_bytes == 3:
                    s = b''.join([s[4 * i + 1 : 4 * i + 4] for i in range(len(s) // 4)])
                if head[1] < self.num_leds:
                    diff = self.num_leds - head[1]
                    s = chr(0) * (diff // 2 * self.led_bytes) + s + chr(0) * ((diff - diff // 2) * self.led_bytes)
                elif head[1] > self.num_leds:
                    hdiff = (head[1] - self.num_leds) // 2
                    s = s[hdiff : hdiff + self.num_leds * self.led_bytes]
                movie.write(s)
        movie.seek(0)
        return (movie, delay)

    def set_static_color(self, red, green, blue):
        # This function can really be removed now, as there are several fuctions for creating patterns
        self.show_pattern(self.make_solid_pattern((red, green, blue)))
