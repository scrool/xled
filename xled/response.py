# -*- coding: utf-8 -*-

from __future__ import absolute_import

import collections

from xled.exceptions import ApplicationError


class ApplicationResponse(collections.Mapping):
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
    def data(self):
        """
        Response content as dict
        """

        if self._data is False:
            # Read the contents.
            if self._content_consumed:
                raise RuntimeError("The content for this response was already consumed")

            if self.status_code == 0 or self.response.raw is None:
                self._data = {}
            else:
                self._data = dict(self.response.json())

            self._content_consumed = True
        return self._data

    def raise_for_status(self):
        """
        Raises :py:exc:`~.exceptions.ApplicationError`, if one occurred.

        :raises ApplicationError: if response cannot be parsed
            as JSON or application status code wasn't success (1000).
        :rtype: None
        """
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
        return "<ApplicationResponse [%s]>" % (self.status_code)
