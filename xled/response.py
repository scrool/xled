# -*- coding: utf-8 -*-

from __future__ import absolute_import

from xled.exceptions import ApplicationError


class ApplicationResponse(object):
    """The :class:`ApplicationResponse <ApplicationResponse>` object, which
    contains a server's response to an HTTP request.
    """

    def __init__(self):
        #: Integer Code of responded application status, e.g. 1000 or 1001
        self.status_code = None

        #: The :class:`requests.Response <Response>` object to which this
        #: is a response.
        self.response = None

        self._dict = False
        self._content_consumed = False

    @property
    def dict(self):
        """
        Response content as dict
        """

        if self._dict is False:
            # Read the contents.
            if self._content_consumed:
                raise RuntimeError("The content for this response was already consumed")

            if self.status_code == 0 or self.response.raw is None:
                self._dict = {}
            else:
                self._dict = dict(self.response.json())

            self._content_consumed = True
        return self._dict

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

    def keys(self):
        return self.dict.keys()

    def __getitem__(self, key):
        return self.dict[key]

    def __iter__(self):
        return iter(self.dict)

    def __len__(self):
        return len(self.dict)

    def __repr__(self):
        return "<ApplicationResponse [%s]>" % (self.status_code)
