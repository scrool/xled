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
from operator import xor

from requests.compat import urljoin

import xled.util
from xled.auth import BaseUrlChallengeResponseAuthSession
from xled.compat import xrange
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

    def firmware_update(self, stage0_sha1sum, stage1_sha1sum):
        """
        Performs firmware update from previously uploaded images

        :param str stage0_sha1sum: SHA1 digest of first stage
        :param str stage1_sha1sum: SHA1 digest of second stage
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {
            "checksum": {
                "stage0_sha1sum": stage0_sha1sum,
                "stage1_sha1sum": stage1_sha1sum,
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
        required_keys = [u"time_now", u"time_off", u"time_on", u"code"]
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
        assert list(app_response.keys()) == [u"code"]

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

    def set_mode(self, mode):
        """
        Sets new LED operation mode.

        :param str mode: Mode to set. One of 'movie', 'demo', 'off'.
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert mode in ("movie", "demo", "off")
        json_payload = {"mode": mode}
        url = urljoin(self.base_url, "led/mode")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)

    def set_led_movie_full(self, movie):
        """
        Uploads movie

        :param movie: file-like object that points to movie file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/movie/full")
        response = self.session.post(
            url, headers={"Content-Type": "application/octet-stream"}, data=movie
        )
        return ApplicationResponse(response)

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
        Sets network mode to Access Point

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

    def update_firmware(self, stage0, stage1):
        """
        Uploads firmware and runs update

        :param stage0: file-like object pointing to stage0 of firmware. Must support seek().
        :param stage1: file-like object pointing to stage1 of firmware. Must support seek().
        :raises ApplicationError: on application error
        :raises HighInterfaceError: on error during update
        """
        fw_stage_sums = [None, None]
        for stage in (0, 1):
            # I don't know how to dynamically construct variable name
            if stage == 0:
                fw_stage_sums[stage] = xled.security.sha1sum(stage0)
            elif stage == 1:
                fw_stage_sums[stage] = xled.security.sha1sum(stage1)
            log.debug("Firmware stage %d SHA1SUM: %r", stage, fw_stage_sums[stage])
            if not fw_stage_sums[stage]:
                msg = "Failed to compute SHA1SUM for firmware stage %d." % (stage)
                raise HighInterfaceError(msg)
                assert False

        stage0.seek(0)
        stage1.seek(0)
        uploaded_stage_sums = [None, None]
        for stage in (0, 1):
            log.debug("Uploading firmware stage %d...", stage)
            # I still don't know how to dynamically construct variable name
            if stage == 0:
                response = self.firmware_0_update(stage0)
            elif stage == 1:
                response = self.firmware_1_update(stage1)
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
            msg = "Firmware SHA1SUMs doesn't match to uploaded SHA1SUMs."
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

        off = device_response["time_on"]
        off_formatted = xled.util.date_from_seconds_after_midnight(off).strftime(
            TIME_FORMAT
        )

        return Timer(now_formatted, on_formatted, off_formatted)

    @staticmethod
    def write_static_movie(file_obj, size, red, green, blue):
        """
        Writes movie of single color

        :param file_obj: file-like object to write movie to.
        :param int size: numbers of triples (RGB) to write to.
        :param red: integer between 0-255 representing red color
        :param green: integer between 0-255 representing green color
        :param blue: integer between 0-255 representing blue color
        """
        assert red in range(0, 256)
        assert green in range(0, 256)
        assert blue in range(0, 256)
        bytes_str = struct.pack(">BBB", red, green, blue)
        for position in xrange(size):
            file_obj.write(bytes_str)

    def set_static_color(self, red, green, blue):
        """
        Sets static color for all leds

        :param red: integer between 0-255 representing red color
        :param green: integer between 0-255 representing green color
        :param blue: integer between 0-255 representing blue color
        """
        assert red in range(0, 256)
        assert green in range(0, 256)
        assert blue in range(0, 256)
        response = self.get_device_info()
        number_of_led = response["number_of_led"]
        with io.BytesIO() as output:
            self.write_static_movie(output, number_of_led, red, green, blue)
            self.led_reset()
            output.seek(0)
            self.set_led_movie_full(output)
            self.set_led_movie_config(1, 1, number_of_led)

    def turn_on(self):
        """
        Turns on the device.
        """
        return self.set_mode("movie")

    def turn_off(self):
        """
        Turns off the device.
        """
        return self.set_mode("off")

    def is_on(self):
        """
        Returns True if device is on
        """
        return self.get_mode()["mode"] != "off"
