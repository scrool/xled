# -*- coding: utf-8 -*-

from __future__ import absolute_import

from xled.exceptions import ApplicationError
from xled.compat import JSONDecodeError, Mapping


class ApplicationResponse(Mapping):
    """The :class:`ApplicationResponse <ApplicationResponse>` object, which
    contains a server's response to an HTTP request.

    :param response: to which this is a response. Can be later set as an
        attribute.
    :type response: :class:`requests.Response <Response>` or None
    """

    def __init__(self, response=None):
        self.response = response

        self._data = False
        self._content_consumed = False

    @property
    def status_code(self):
        """Integer Code of responded application status, e.g. 1000 or 1001"""
        return self.data.get("code", None)

    @property
    def ok(self):
        """
        Returns True if :attr:`status_code` is 1000, False if not.

        First this attribute checks if parent response is ok. Then it checks if
        application response can be determined and finally if
        :attr:`status_code` is 1000.
        """
        if not self.response.ok:
            return False
        try:
            self.raise_for_status(propagate=False)
        except ApplicationError:
            return False
        return True

    @property
    def data(self):
        """
        Response content as dict
        """

        if self._data is False:
            # Read the contents.
            if self._content_consumed:
                raise RuntimeError("The content for this response was already consumed")

            if self.response is None:
                raise RuntimeError(
                    "No response to create application response data from"
                )

            if self.response.raw is None:
                self._data = {}
            else:
                self.response.raise_for_status()
                try:
                    json_data = self.response.json()
                except JSONDecodeError:
                    msg = "Failed to decode application data: %r" % self.response.text
                    raise ApplicationError(msg, response=self.response)
                self._data = dict(json_data)

            self._content_consumed = True
        return self._data

    def raise_for_status(self, propagate=True):
        """
        Raises :py:exc:`~.exceptions.ApplicationError`, if one occurred.

        :param bool propagate: check status of underlying
            :class:`requests.Response` as well.
        :raises ApplicationError: if response cannot be parsed
            as JSON or application status code wasn't success (1000).
        :rtype: None
        """
        if propagate:
            self.response.raise_for_status()

        if self.status_code is None:
            msg = "Status code not determined."
            raise ApplicationError(msg, response=self.response)

        msg = ""
        if self.status_code == 1000:
            return
        elif isinstance(self.status_code, int):
            msg = "Application error code: {}".format(self.status_code)
            raise ApplicationError(msg, response=self.response)

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        try:
            self.raise_for_status(propagate=False)
        except ApplicationError:
            status = None
        else:
            status = self.status_code
        return "<ApplicationResponse [%s]>" % status


def build_response(response):
    """Creates ApplicationResponse object out of Requests response

    :param response: to which this is a response. Can be later set as an
        attribute.
    :type response: :class:`requests.Response <Response>` or None
    :rtype: :class:`ApplicationResponse`
    """
    app_response = ApplicationResponse()
    app_response.response = response
    return app_response
