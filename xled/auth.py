# -*- coding: utf-8 -*-

"""
xled.auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom authentication handler and authenticated session to be used with
:class:`requests.Session`
"""

from __future__ import absolute_import

import base64
import logging
import time

import requests
from requests import Request
from requests.auth import AuthBase
from requests.compat import urlparse
from requests_toolbelt.sessions import BaseUrlSession

import xled.security
from xled.exceptions import (
    ApplicationError,
    AuthenticationError,
    TokenExpiredError,
    ValidationError,
)
from xled.response import ApplicationResponse
from xled.security import generate_challenge

log = logging.getLogger(__name__)


AUTH_HEADER_NAME = "X-Auth-Token"


class ChallengeResponseAuth(AuthBase):
    def __init__(self, login_url, verify_url, hw_address=None):
        self.login_url = login_url
        self.verify_url = verify_url
        self.hw_address = hw_address

        # populated after first request
        self.challenge = None
        self.challenge_response = None
        self.authentication_token = None

    def validate_challenge_response(self):
        if not self.hw_address:
            msg = (
                "validate_challenge_response(): Cannot verify "
                "challenge-response without HW address."
            )
            log.warning(msg)
            return None

        expected = xled.security.make_challenge_response(
            self.challenge, self.hw_address
        )
        if expected != self.challenge_response:
            msg = (
                "validate_challenge_response(): login sent "
                "challenge-response: %r. But %r was expected."
            )
            log.error(msg, self.challenge_response, expected)
            return False
        msg = "validate_challenge_response(): challenge-response is correct."
        log.debug(msg)
        return True

    def send_challenge(self, response, challenge):
        host = urlparse(response.url).hostname
        schema = urlparse(response.url).scheme
        url = "%s://%s%s" % (schema, host, self.login_url)
        b64_challenge = base64.b64encode(challenge).decode("utf-8")
        body = {"challenge": b64_challenge}
        r2 = requests.Request(method="POST", url=url, json=body)
        prep = r2.prepare()
        _r = response.connection.send(prep)
        if _r.status_code != 200:
            msg = "send_challenge(): login status code: %s"
            log.error(msg, _r.status_code)
            return False
        content = _r.json()
        if content[u"code"] != 1000:
            msg = "send_challenge(): login return code: %s"
            log.error(msg, content[u"code"])
            return False
        self.challenge_response = content["challenge-response"]
        self.authentication_token = content["authentication_token"]
        return True

    def send_challenge_response(self, response):
        host = urlparse(response.url).hostname
        schema = urlparse(response.url).scheme
        url = "%s://%s%s" % (schema, host, self.verify_url)
        headers = {"X-Auth-Token": self.authentication_token}
        body = {u"challenge-response": self.challenge_response}
        r2 = requests.Request(method="POST", url=url, headers=headers, json=body)
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

        challenge = xled.security.generate_challenge()
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

        response.request.headers["X-Auth-Token"] = self.authentication_token
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
        num_401s = kwargs.pop("num_401s", 0)

        # If response is not 4xx, do not auth
        if not 400 <= response.status_code < 500:
            log.debug(
                "handle_response(): Not authenticating request because status is %s",
                response.status_code,
            )
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
        response.request.deregister_hook("response", self.handle_response)

    def __call__(self, request):
        if self.authentication_token:
            log.debug(
                "Adding authentication token %s to request", self.authentication_token
            )
            request.headers["X-Auth-Token"] = self.authentication_token
        request.register_hook("response", self.handle_response)
        try:
            self.pos = request.body.tell()
        except AttributeError:
            # In the case of ChallengeResponseAuth being reused and the body
            # of the previous request was a file-like object, pos has
            # the file position of the previous body. Ensure it's set to
            # None.
            self.pos = None
        return request


class BaseUrlChallengeResponseAuthSession(BaseUrlSession):
    """Extension to :class:`requests_toolbelt.BaseUrlSession` to provide authentication.

    Any request used with this session gets authentication token added.
    Authentication token can be fetched even separately.
    """

    def __init__(self, hw_address=None, client=None, auto_refresh_token=True, **kwargs):
        """Construct a new client session.

        :param str hw_address: Hardware address of server. Used to validation during
                               login phase.
        :param client: Object with :class:`ClientApplication` interface.
                       login phase.
        :param bool auto_refresh_token: (optional) if token is found expired
                                        automatically request new one.
        :param kwargs: Arguments to pass to the BaseUrlSession initializer.
                       Most useful is `base_url`.
        """
        self.hw_address = hw_address
        self.client = client or ClientApplication()
        self.auto_refresh_token = auto_refresh_token
        super(BaseUrlChallengeResponseAuthSession, self).__init__(**kwargs)

    def prepare_request_challenge(self):
        """Creates prepared request to send challenge

        :return: prepared request
        :rtype: requests.PreparedRequest
        """
        request = Request("POST", self.challenge_url)
        prepped = self.prepare_request(request)
        request = self.client.prepare_request_challenge(prepped)
        return request

    def prepare_request_verify(self):
        """Creates prepared request to send verification

        :return: prepared request
        :rtype: requests.PreparedRequest
        """
        request = Request("POST", self.verify_url)
        prepped = self.prepare_request(request)
        request = self.client.prepare_request_verify(prepped)
        return request

    @property
    def challenge_url(self):
        """Full URL of login endpoint

        :return: String with full url
        :rtype: str
        """
        return self.create_url("login")

    @property
    def verify_url(self):
        """Full URL of verify endpoint

        :return: Full URL.
        :rtype: str
        """
        return self.create_url("verify")

    def fetch_token(self):
        """Main authentication method that fetches new token

        :return: Token as string.
        :rtype: str
        """
        prepared = self.prepare_request_challenge()
        response = self.send(prepared)
        self.client.parse_response_challenge(response)
        self.client.challenge_response_valid(self.hw_address)

        prepared = self.prepare_request_verify()
        response = self.send(prepared)
        self.client.parse_response_verify(response)

        return self.client.authentication_token

    def add_token(self, headers=None):
        """Adds token header to dictionary with headers

        :param dict headers: Optional initial dictionary with headers.
        :return: Dict with added authentication header.
        :rtype: dict
        :raises TokenExpiredError: If token is expected to be expired.
        """
        assert self.client.authentication_token
        if self.client.token_expired:
            raise TokenExpiredError()
        headers = headers or {}
        headers[AUTH_HEADER_NAME] = self.access_token
        return headers

    @property
    def authorized(self):
        """Boolean that indicates whether this session has an ChallengeResponse
        token or not. If `self.authorized` is True, you can reasonably expect
        ChallengeResponse-protected requests to the resource to succeed. If
        `self.authorized` is False, you need the user to go through the
        ChallengeResponse authentication dance before
        ChallengeResponse-protected requests to the resource will succeed.
        :rtype: bool
        """
        return bool(self.access_token)

    @property
    def access_token(self):
        """Current authentication token if exists. None if it wasn't fetched yet."""
        return getattr(self.client, "authentication_token", None)

    @access_token.setter
    def access_token(self, value):
        self.client.authentication_token = value

    def request(self, method, url, headers=None, withhold_token=False, **kwargs):
        """Main request method of the session

        Adds authentication to method from
        :class:`requests_toolbelt.BaseUrlSession`. Takes auto_refresh_token in
        mind.

        :param dict withhold_token: If boolean is True authentication token
                                    isn't added to the request.
        :rtype: requests.Response
        """
        for attempt in range(2):
            if not withhold_token:
                headers = self.add_authorization(headers)

            log.debug("Requesting url %s using method %s.", url, method)
            log.debug("Supplying headers %s", headers)
            log.debug("Passing through key word arguments %s.", kwargs)
            response = super(BaseUrlChallengeResponseAuthSession, self).request(
                method, url, headers=headers, **kwargs
            )
            if response.status_code == 401:
                log.warning(
                    "Unexpected HTTP status code 401 to request with added token."
                )
                self.access_token = False
                log.debug("Token invalidated.")
            else:
                break
        return response

    def add_authorization(self, headers):
        """Returns headers with added authorization

        :param dict headers: user supplied request headers
        :rtype: dict
        """
        if not self.authorized:
            self.fetch_token()

        if self.access_token:
            for attempt in range(2):
                try:
                    headers = self.add_token(headers)
                except TokenExpiredError:
                    if not self.auto_refresh_token:
                        raise
                    log.debug("Auto refresh token is set, attempting to refresh.")
                    self.fetch_token()
                    if not self.access_token:
                        log.error("Failed to refresh token.")
                        raise AuthenticationError()
                else:
                    break
            else:
                log.error("Failed to add token.")
                raise AuthenticationError()
        return headers


class ValidatingClientMixin(object):
    """Mixin adds functionality to :class:`ClientApplication` to authenticate server"""

    def challenge_response_valid(self, hw_address=None):
        """Verifies server with hardware address returned correct challenge response

        Creates challenge-response for server's hardware address, challenge and
        shared password and compares it with stored challenge-response.

        :param str hw_address: Hardware address of a server.
        :return: If challenge-response is valid returns True. If it cannot be
                 verified returns None.
        :rtype: bool or None
        :raises ValidationError: if chalenge-response is invalid
        """
        if not hw_address:
            msg = "Can not validate challenge-response without hw_address."
            log.debug(msg)
            return None

        expected = xled.security.make_challenge_response(self._challenge, hw_address)
        if expected != self._challenge_response:
            msg = (
                "challenge-response invalid. "
                "Received challenge-response: %r but %r was expected."
            )
            log.error(msg, self._challenge_response, expected)
            raise ValidationError()

        msg = "challenge-response is correct."
        log.debug(msg)
        return True


class ClientApplication(ValidatingClientMixin):
    def __init__(self, challenge=None):
        self.authentication_token = None
        self.expires_at = None

        self.challenge = challenge or generate_challenge
        self._challenge = challenge

        self._challenge = None
        self._authentication_token = None
        self._challenge_response = None
        self._expires_in = None

    def new_challenge(self):
        """Generates a challenge string to be used in authorizations."""
        try:
            self._challenge = self.challenge()
            log.debug("Generated new state %r.", self._challenge)
        except TypeError:
            self._challenge = self.challenge
            log.debug("Re-using previously supplied challenge %s.", self._challenge)
        return self._challenge

    @property
    def token_expired(self):
        if self.expires_at and self.expires_at < time.time():
            log.info("Token has expired.")
            return True
        return False

    @property
    def token_valid(self):
        return self.authentication_token and not self.token_expired

    def _add_token(self, headers=None):
        """Adds authentication token that haven't been verified yet to headers"""

        assert self._authentication_token
        headers = headers or {}
        headers[AUTH_HEADER_NAME] = self._authentication_token
        return headers

    def prepare_request_challenge(self, request):
        """Modifies prepared request so it can be sent to login

        :param: requests.PreparedRequest request prepared request to modify
        :return: Modified prepared request
        :rtype: requests.PreparedRequest
        """

        challenge = self.new_challenge()
        self._authentication_token = None
        self._challenge_response = None
        self._expires_in = None
        log.debug("ClientApplication(): Challenge: %s", repr(challenge))
        b64_challenge = base64.b64encode(challenge).decode("utf-8")
        request.prepare_body(None, None, json={"challenge": b64_challenge})
        return request

    def populate_token_attributes(self, response):
        """Fetches token attributes from application response

        :param: app_response response Response from login endpoint.
        :type: application_response :class:`~xled.response.ApplicationResponse`
        """
        if "authentication_token" in response:
            self._authentication_token = response.get("authentication_token")

        if "challenge-response" in response:
            self._challenge_response = response.get("challenge-response")

        if "authentication_token_expires_in" in response:
            self._expires_in = response.get("authentication_token_expires_in")
            self.expires_at = time.time() + int(self._expires_in)

    def parse_response_challenge(self, response, **kwargs):
        """Modifies prepared request so challenge can be sent to login

        :param: requests.PreparedRequest response prepared request
        :return: Modified prepared request
        :rtype: requests.PreparedRequest
        :raises AuthenticationError: if application response isn't valid
        """
        app_response = ApplicationResponse(response)
        try:
            app_response.raise_for_status()
        except ApplicationError:
            log.error(
                "receive_authentication_token(): login failed: %r" % app_response.data
            )
            raise AuthenticationError()

        self.populate_token_attributes(app_response)
        log.debug(
            "receive_authentication_token(): got token: %s", self._authentication_token
        )
        return response

    def prepare_request_verify(self, request):
        """Modifies prepared request so it can be sent to verify challenge

        :param: requests.PreparedRequest request prepared request to modify
        :return: Modified prepared request
        :rtype: requests.PreparedRequest
        """

        assert self._authentication_token
        assert self._challenge_response
        token_headers = self._add_token()
        request.prepare_headers(token_headers)
        request.prepare_body(
            None, None, json={"challenge_response": self._challenge_response}
        )
        return request

    def parse_response_verify(self, response, **kwargs):
        """Process response from verify call

        This is last step to be able to use token to authenticate.

        :param: requests.Response response Response to process.
        :return: Same response that was used as parameter
        :rtype: requests.Response
        :raises AuthenticationError: if application response isn't valid
        """
        app_response = ApplicationResponse(response)
        try:
            app_response.raise_for_status()
        except ApplicationError:
            log.error("receive_authentication_token(): verify failed")
            return AuthenticationError()

        self._challenge_response = None
        self.authentication_token = self._authentication_token
        self._authentication_token = None
        return response
