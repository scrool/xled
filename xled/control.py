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
import base64
from operator import xor

from requests.compat import urljoin

import xled.util
import xled.security
from xled.udp_client import UDPClient
from xled.auth import BaseUrlChallengeResponseAuthSession
from xled.compat import xrange
from xled.exceptions import HighInterfaceError
from xled.response import ApplicationResponse

log = logging.getLogger(__name__)

#: UDP port to send realtime frames to
REALTIME_UDP_PORT_NUMBER = 7777

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
        self._udpclient = None
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

    @property
    def udpclient(self):
        """
        Client for sending UDP packets to the realtime port

        :return: the UDP client
            :py:class:`~.udp_client.UDPClient()`.
        :rtype: udp_client.UDPClient
        """
        if not self._udpclient:
            self._udpclient = UDPClient(REALTIME_UDP_PORT_NUMBER, self.host)
            assert self._udpclient
        return self._udpclient

    def check_status(self):
        """
        Checks that the device is online and responding

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "status")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def delete_movies(self):
        """
        Remove all uploaded movies.

        .. seealso:: :py:meth:`get_movies()` :py:meth:`set_movies_new()` :py:meth:`set_movies_full()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "movies")
        response = self.session.delete(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def delete_playlist(self):
        """
        Clears the playlist

        .. seealso:: :py:meth:`get_playlist()` :py:meth:`set_playlist()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "playlist")
        response = self.session.delete(url)
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
        json_payload = {
            "checksum": {
                "stage0_sha1sum": stage0_sha1sum,
            }
        }
        if stage1_sha1sum is not None:
            json_payload["checksum"]["stage1_sha1sum"] = stage1_sha1sum
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
        required_keys = [u"version", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
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
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
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
        required_keys = [u"strings", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_led_effects_current(self):
        """
        Gets the current effect index

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/effects/current")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_led_effects(self):
        """
        Gets the number of effects and their unique_ids

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/effects")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"effects_number", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_led_layout(self):
        """
        Gets the physical layout of the leds

        .. seealso:: :py:meth:`set_led_layout()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/layout/full")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"source", u"synthesized", u"coordinates", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
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
        required_keys = [u"frame_delay", u"leds_number", u"frames_number", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
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

    def get_movies(self):
        """
        Gets list of uploaded movies.

        .. seealso:: :py:meth:`delete_movies()` :py:meth:`set_movies_new()` :py:meth:`set_movies_full()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "movies")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"movies", u"available_frames", u"max_capacity", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_movies_current(self):
        """
        Gets the movie id of the currently played movie in the movie list

        .. seealso:: :py:meth:`set_movies_current()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "movies/current")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"id", u"unique_id", u"name", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_mqtt_config(self):
        """
        Gets the mqtt configuration parameters

        .. seealso:: :py:meth:`set_mqtt_config()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "mqtt/config")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
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
        required_keys = [u"mode", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_playlist(self):
        """
        Gets the current playlist

        .. seealso:: :py:meth:`delete_playlist()` :py:meth:`set_playlist()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "playlist")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"entries", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_playlist_current(self):
        """
        Gets the movie id of the currently played movie in the playlist

        .. seealso:: :py:meth:`set_playlist_current()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "playlist/current")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"id", u"unique_id", u"name", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def get_saturation(self):
        """
        Gets current saturation level and if desaturation is applied

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/out/saturation")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code", u"mode", u"value"]
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
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def network_scan(self):
        """
        Initiate WiFi network scan

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "network/scan")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def network_scan_results(self):
        """
        Get results of WiFi network scan

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "network/scan_results")
        response = self.session.get(url)
        app_response = ApplicationResponse(response)
        required_keys = [u"networks", u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_brightness(self, brightness=None, enabled=True, relative=False):
        """
        Sets new brightness or enable/disable brightness dimming

        :param brightness: new brightness in range of 0..100 or a relative
                           change in -100..100 or None if no change is requested
        :param bool enabled: set to False if no dimming should be applied
        :param bool relative: set to True to make a relative change
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        if brightness is not None:
            if relative:
                assert brightness in range(-100, 101)
                json_payload = {"value": brightness, "type": "R"}  # Relative
            else:
                assert brightness in range(0, 101)
                json_payload = {"value": brightness, "type": "A"}  # Absolute
        if enabled:
            json_payload["mode"] = "enabled"
        else:
            json_payload["mode"] = "disabled"
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
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        assert len(name) <= 32
        json_payload = {"name": name}
        url = urljoin(self.base_url, "device_name")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_led_effects_current(self, effect_id):
        """
        Sets the current effect of effect mode

        :param int effect_id: id of effect
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {"effect_id": effect_id}
        url = urljoin(self.base_url, "led/effects/current")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_led_layout(self, source, coordinates, synthesized=False):
        """
        Sets the physical layout of the leds

        :param str source: 2d, 3d, or linear
        :param list coordinates: list of dictionaries with keys 'x', 'y', and 'z'
        :param bool synthesized: presumably whether it is synthetic or real coordinates
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        assert source in ["linear", "2d", "3d"]
        assert isinstance(coordinates, list)
        json_payload = {
            "source": source,
            "coordinates": coordinates,
            "synthesized": synthesized,
        }
        url = urljoin(self.base_url, "led/layout/full")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

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
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

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
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_mode(self, mode):
        """
        Sets new LED operation mode.

        :param str mode: Mode to set. One of 'movie', 'playlist', 'rt', 'demo', 'effect' or 'off'.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        assert mode in ("movie", "playlist", "rt", "demo", "effect", "off")
        json_payload = {"mode": mode}
        url = urljoin(self.base_url, "led/mode")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_movies_current(self, movie_id):
        """
        Sets which movie in the movie list to play

        .. seealso:: :py:meth:`get_movies_current()`

        :param int movie_id: id of movie to play
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {"id": movie_id}
        url = urljoin(self.base_url, "movies/current")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_movies_full(self, movie):
        """
        Uploads a movie to the movie list

        Presumes that 'set_movies_new' has been called earlier with the movie params.

        .. seealso:: :py:meth:`get_movies()` :py:meth:`delete_movies()` :py:meth:`set_movies_new()`

        :param movie: file-like object that points to movie file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "movies/full")
        head = {"Content-Type": "application/octet-stream"}
        response = self.session.post(url, headers=head, data=movie)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_movies_new(self, name, uid, dtype, nleds, nframes, fps):
        """
        Prepares the upload of a new movie to the movie list by setting its parameters

        .. seealso:: :py:meth:`get_movies()` :py:meth:`delete_movies()` :py:meth:`set_movies_full()`

        :param str name: name of new movie
        :param str uid: unique id of new movie
        :param str dtype: descriptor_type, one of rgb_raw, rgbw_raw, or aww_raw
        :param int nleds: number of leds
        :param int nframes: number of frames
        :param int fps: frames per second of the new movie
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        assert len(name) <= 32
        json_payload = {
            "name": name,
            "unique_id": uid,
            "descriptor_type": dtype,
            "leds_per_frame": nleds,
            "frames_number": nframes,
            "fps": fps,
        }
        url = urljoin(self.base_url, "movies/new")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_mqtt_config(
        self,
        broker_host=None,
        broker_port=None,
        client_id=None,
        user=None,
        interval=None,
    ):
        """
        Sets the mqtt configuration parameters

        .. seealso:: :py:meth:`get_mqtt_config()`

        :param str broker_host: optional broker host
        :param int broker_port: optional broker port
        :param str client_id: optional client_id
        :param str user: optional user name
        :param int interval: optional keep alive interval
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {}
        if broker_host:
            json_payload["broker_host"] = broker_host
        if broker_port:
            json_payload["broker_port"] = broker_port
        if client_id:
            json_payload["client_id"] = client_id
        if interval is not None:
            json_payload["keep_alive_interval"] = interval
        if user:
            json_payload["user"] = user
        if not json_payload:
            msg = "At least some value needs to be set"
            raise ValueError(msg)
        url = urljoin(self.base_url, "mqtt/config")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_network_mode_ap(self, password=None):
        """
        Sets network mode to Access Point

        If password is given, changes the Access Point password
        (after which you have to connect again with the new password)

        :param str password: new password to set
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {"mode": 2}
        if password:
            json_payload["ap"] = {"password": password, "enc": 4}
        url = urljoin(self.base_url, "network/status")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_network_mode_station(self, ssid=None, password=None):
        """
        Sets network mode to Station

        The first time you need to provide an ssid and password for
        the WIFI to connect to.

        :param str ssid: SSID of the access point to connect to
        :param str password: password to use
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {"mode": 1}
        if ssid and password:
            assert self.hw_address
            encpassword = xled.security.encrypt_wifi_password(password, self.hw_address)
            json_payload["station"] = {
                "dhcp": 1,
                "ssid": ssid,
                "encpassword": encpassword,
            }
        else:
            assert not ssid and not password
        url = urljoin(self.base_url, "network/status")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_playlist(self, entries):
        """
        Sets a new playlist

        .. seealso:: :py:meth:`get_playlist()` :py:meth:`delete_playlist()`

        :param list entries: list of playlist entries each with keys "unique_id" and "duration"
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        assert isinstance(entries, list)
        json_payload = {"entries": entries}
        url = urljoin(self.base_url, "playlist")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_playlist_current(self, movie_id):
        """
        Sets which movie in the playlist to play

        .. seealso:: :py:meth:`get_playlist_current()`

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        json_payload = {"id": movie_id}
        url = urljoin(self.base_url, "playlist/current")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_rt_frame_rest(self, frame):
        """
        Uploads a frame in rt-mode, using the ordinary restful protocol

        :param frame: file-like object that points to frame file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, "led/rt/frame")
        response = self.session.post(
            url, headers={"Content-Type": "application/octet-stream"}, data=frame
        )
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

    def set_rt_frame_socket(self, frame, version, leds_number=None):
        """
        Uploads a frame in rt-mode, over an UDP socket.
        This is much faster than the restful protocol.

        :param frame: file-like object representing the frame
        :param version: use protocol version 1, 2 or 3
        :param int leds_number: the number of leds (only used in version 1)
        :rtype: None
        """
        if version == 1:
            # Send single frame, generation I
            packet = bytearray(b"\x01")
            packet.extend(base64.b64decode(self.session.access_token))
            packet.extend(struct.pack(">B", leds_number))
            packet.extend(frame.read())
            self.udpclient.send(packet)
        elif version == 2:
            # Send single frame, generation II pre 2.4.14
            packet = bytearray(b"\x02")
            packet.extend(base64.b64decode(self.session.access_token))
            packet.extend(b"\x00")
            packet.extend(frame.read())
            self.udpclient.send(packet)
        else:
            # Send multi frame, generation II post 2.4.14
            packet_size = 900
            data_packet = frame.read(packet_size)
            i = 0
            while data_packet:
                packet = bytearray(b"\x03")
                packet.extend(base64.b64decode(self.session.access_token))
                packet.extend(b"\x00\x00")
                packet.extend(struct.pack(">B", i))
                packet.extend(data_packet)
                self.udpclient.send(packet)
                data_packet = frame.read(packet_size)
                i += 1

    def set_saturation(self, saturation=None, enabled=True, relative=False):
        """
        Sets new saturation or enable/disable desaturation

        :param saturation: new saturation in range of 0..100 or a relative
                           change in -100..100 or None if no change is requested
        :param bool enabled: set to False if no desaturation should be applied
        :param bool relative: set to True to make a relative change
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        if saturation is not None:
            if relative:
                assert saturation in range(-100, 101)
                json_payload = {"value": saturation, "type": "R"}  # Relative
            else:
                assert saturation in range(0, 101)
                json_payload = {"value": saturation, "type": "A"}  # Absolute
        else:
            json_payload = {}
        if enabled:
            json_payload["mode"] = "enabled"
        else:
            json_payload["mode"] = "disabled"
        url = urljoin(self.base_url, "led/out/saturation")
        response = self.session.post(url, json=json_payload)
        app_response = ApplicationResponse(response)
        required_keys = [u"code"]
        assert all(key in app_response.keys() for key in required_keys)
        return app_response

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
        :rtype: :class:`~xled.response.ApplicationResponse`
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
        return app_response


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
