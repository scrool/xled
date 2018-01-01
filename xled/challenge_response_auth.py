# -*- coding: utf-8 -*-

"""
xled.challenge_response_auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom authentication handler to be used with :class:`requests.Session`
"""

from __future__ import absolute_import

import base64
import logging
import os

import xled.security

import requests
from requests.auth import AuthBase
from requests.compat import urlparse


log = logging.getLogger(__name__)


class ChallengeResponseAuth(AuthBase):
    def __init__(self, login_url, verify_url, hw_address=None):
        self.login_url = login_url
        self.verify_url = verify_url
        self.hw_address = hw_address

        # populated after first request
        self.challenge = None
        self.challenge_response = None
        self.authentication_token = None

    def generate_challenge(self):
        """
        Generates random challenge string

        :rtype: str
        """
        self.challenge = os.urandom(32)
        return self.challenge

    def validate_challenge_response(self):
        if not self.hw_address:
            msg = ("validate_challenge_response(): Cannot verify "
                   "challenge-response without HW address.")
            log.warning(msg)
            return None

        expected = xled.security.make_challenge_response(self.challenge,
                                                         self.hw_address)
        if expected != self.challenge_response:
            msg = ("validate_challenge_response(): login sent "
                   "challenge-response: %r. But %r was expected.")
            log.error(msg, self.challenge_response, expected)
            return False
        msg = "validate_challenge_response(): challenge-response is correct."
        log.debug(msg)
        return True

    def send_challenge(self, response, challenge):
        host = urlparse(response.url).hostname
        schema = urlparse(response.url).scheme
        url = '%s://%s%s' % (schema, host, self.login_url)
        b64_challenge = base64.b64encode(challenge)
        body = {'challenge': b64_challenge}
        r2 = requests.Request(method='POST', url=url, json=body)
        prep = r2.prepare()
        _r = response.connection.send(prep)
        if _r.status_code != 200:
            msg = "send_challenge(): login status code: %s"
            log.error(msg, _r.status_code)
            return False
        content = _r.json()
        if content[u'code'] != 1000:
            msg = "send_challenge(): login return code: %s"
            log.error(msg, content[u'code'])
            return False
        self.challenge_response = content['challenge-response']
        self.authentication_token = content['authentication_token']
        return True

    def send_challenge_response(self, response):
        host = urlparse(response.url).hostname
        schema = urlparse(response.url).scheme
        url = '%s://%s%s' % (schema, host, self.verify_url)
        headers = {'X-Auth-Token': self.authentication_token}
        body = {u"challenge-response": self.challenge_response}
        r2 = requests.Request(method='POST', url=url, headers=headers,
                              json=body)
        prep = r2.prepare()
        _r = response.connection.send(prep)
        if _r.status_code != 200:
            return False
        return True

    def authenticate(self, response, **kwargs):
        """Handles user authentication with challenge-response"""

        # Consume the content so we can reuse the connection for the next
        # request.
        response.content
        response.raw.release_conn()

        challenge = self.generate_challenge()
        log.debug("authenticate(): Challenge: %s", repr(challenge))
        login_successfull = self.send_challenge(response, challenge)
        if not login_successfull:
            return response

        cr_correct = self.validate_challenge_response()
        if cr_correct is False:
            return response

        verify_successfull = self.send_challenge_response(response)
        if not verify_successfull:
            return response

        response.request.headers['X-Auth-Token'] = self.authentication_token
        _r = response.connection.send(response.request, **kwargs)
        _r.history.append(response)

        log.debug("authenticate(): returning %s", _r)
        return _r

    def handle_401(self, response, **kwargs):
        """
        Handles 401's, attempts to use challenge-response authentication
        """

        log.debug("handle_401(): Handling: 401")
        _r = self.authenticate(response, **kwargs)
        log.debug("handle_401(): returning %s", _r)
        return _r

    def handle_response(self, response, **kwargs):
        """
        Takes the given response and tries challenge-auth, as needed.
        """
        num_401s = kwargs.pop('num_401s', 0)

        # If response is not 4xx, do not auth
        if not 400 <= response.status_code < 500:
            log.debug('handle_response(): Not authenticating request '
                      'because status is %s', response.status_code)
            return response

        if response.status_code == 401 and num_401s < 2:
            # 401 Unauthorized. Handle it, and if it still comes back as 401,
            # that means authentication failed.
            _r = self.handle_401(response, **kwargs)
            log.debug("handle_response(): returning %s", _r)
            log.debug("handle_response() has seen %d 401 responses", num_401s)
            num_401s += 1
            return self.handle_response(_r, num_401s=num_401s, **kwargs)
        elif response.status_code == 401 and num_401s >= 2:
            # Still receiving 401 responses after attempting to handle them.
            # Authentication has failed. Return the 401 response.
            log.debug("handle_response(): returning 401 %s", response)
        return response

    def deregister(self, response):
        """
        Deregisters the response handler
        """
        response.request.deregister_hook('response', self.handle_response)

    def __call__(self, request):
        if self.authentication_token:
            log.debug('Adding authentication token %s to request',
                      self.authentication_token)
            request.headers['X-Auth-Token'] = self.authentication_token
        request.register_hook('response', self.handle_response)
        try:
            self.pos = request.body.tell()
        except AttributeError:
            # In the case of ChallengeResponseAuth being reused and the body
            # of the previous request was a file-like object, pos has
            # the file position of the previous body. Ensure it's set to
            # None.
            self.pos = None
        return request
