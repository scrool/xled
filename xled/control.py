# -*- coding: utf-8 -*-

"""
xled.control
~~~~~~~~~~~~~

This module contains interface to control specific device

.. seealso::

    :doc:`rest_api`
        for more details about API that is used by the application.

    :doc:`protocol_details`
        for various operations.
"""

from __future__ import absolute_import

import logging

import requests
from requests.compat import urljoin

import xled.util
from xled.challenge_response_auth import ChallengeResponseAuth
from xled.response import ApplicationResponse
from xled.security import encrypt_wifi_password

log = logging.getLogger(__name__)


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
            self._base_url = 'http://{}/xled/v1/'.format(self.host)
            assert self._base_url
        return self._base_url

    @property
    def session(self):
        """
        Session object to operate on

        :return: session object with auth
            :py:class:`~.challenge_response_auth.ChallengeResponseAuth()`.
        :rtype: requests.Session
        """
        if not self._session:
            s = requests.Session()
            s.auth = ChallengeResponseAuth(
                login_url='/xled/v1/login',
                verify_url='/xled/v1/verify',
                hw_address=self.hw_address
            )
            self._session = s
            assert self._session
        return self._session

    def _build_response(self, response):
        app_response = ApplicationResponse()
        app_response.response = response
        app_response.status_code = getattr(app_response, 'code', None)
        return app_response

    def firmware_0_update(self, firmware):
        """
        Uploads first stage of the firmware

        :param firmware: file-like object that points to firmware file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, 'fw/0/update')
        response = self.session.post(url, data=firmware)
        app_response = self._build_response(response)
        return app_response

    def firmware_1_update(self, firmware):
        """
        Uploads second stage of the firmware

        :param firmware: file-like object that points to firmware file.
        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, 'fw/1/update')
        response = self.session.post(url, data=firmware)
        app_response = self._build_response(response)
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
            'stage0_sha1sum': stage0_sha1sum,
            'stage1_sha1sum': stage1_sha1sum,
        }
        url = urljoin(self.base_url, 'fw/update')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        return app_response

    def firmware_version(self):
        """
        Gets firmware version

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, 'fw/version')
        response = self.session.get(url)
        app_response = self._build_response(response)
        return app_response

    def get_device_info(self):
        """
        Gets detailed information about device

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, 'gestalt')
        response = self.session.get(url)
        app_response = self._build_response(response)
        return app_response

    def get_device_name(self):
        """
        Gets device name.

        .. seealso:: :py:meth:`set_device_name()`

        :raises ApplicationError: on application error
        :return: current device name.
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, 'device_name')
        response = self.session.get(url)
        app_response = self._build_response(response)
        assert sorted(app_response.keys()) == [u'code', u'name']
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
        url = urljoin(self.base_url, 'led/mode')
        response = self.session.get(url)
        app_response = self._build_response(response)
        assert sorted(app_response.keys()) == [u'code', u'mode']
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
        url = urljoin(self.base_url, 'timer')
        response = self.session.get(url)
        app_response = self._build_response(response)
        assert sorted(app_response.keys()) == [u'time_now', u'time_off',
                                               u'time_on']
        return app_response

    def led_reset(self):
        """
        Resets LED

        :raises ApplicationError: on application error
        :rtype: None
        """
        url = urljoin(self.base_url, 'led/reset')
        response = self.session.get(url)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

    def network_scan(self):
        """
        Initiate WiFi network scan

        :raises ApplicationError: on application error
        :rtype: None
        """
        url = urljoin(self.base_url, 'network/scan')
        response = self.session.get(url)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

    def network_scan_results(self):
        """
        Get results of WiFi network scan

        :raises ApplicationError: on application error
        :rtype: :class:`~xled.response.ApplicationResponse`
        """
        url = urljoin(self.base_url, 'network/scan_results')
        response = self.session.get(url)
        app_response = self._build_response(response)
        return app_response

    def set_device_name(self, name):
        """
        Sets new device name

        :param str name: new device name
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert len(name) <= 32
        json_payload = {'name': name}
        url = urljoin(self.base_url, 'device_name')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

    def set_led_movie_config(self, frame_delay, frames_number, leds_number):
        """
        Performs firmware update from previously uploaded images

        :param int frame_delay: speed of movie
        :param int leds_number: total number of LEDs
        :param int frames_number: total number of frames
        :raises ApplicationError: on application error
        :rtype: None
        """
        json_payload = {
            'frame_delay': frame_delay,
            'frames_number': frames_number,
            'leds_number': leds_number
        }
        url = urljoin(self.base_url, 'led/movie/config')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

    def set_mode(self, mode):
        """
        Sets new LED operation mode.

        :param str mode: Mode to set. One of 'move', 'demo', 'off'.
        :raises ApplicationError: on application error
        :rtype: None
        """
        assert mode in ('movie', 'demo', 'off')
        json_payload = {'mode': mode}
        url = urljoin(self.base_url, 'led/mode')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

    def set_network_mode_ap(self):
        """
        Sets network mode to Access Point

        :raises ApplicationError: on application error
        :rtype: None
        """
        json_payload = {
            'mode': 2
        }
        url = urljoin(self.base_url, 'network/status')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

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
            'mode': 1,
            'station': {
                'dhcp': 1,
                'ssid': ssid,
                'encpassword': encpassword
            }
        }
        url = urljoin(self.base_url, 'network/status')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']

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
            log.debug('Setting time now to %s', time_now)

        json_payload = {
            'time_on': time_on,
            'time_off': time_off,
            'time_now': time_now,

        }
        url = urljoin(self.base_url, 'timer')
        response = self.session.post(url, json=json_payload)
        app_response = self._build_response(response)
        assert app_response.keys() == [u'code']
