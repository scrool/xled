# -*- coding: utf-8 -*-


class XledException(Exception):
    def __init__(self, *args):
        super(XledException, self).__init__(*args)


class ApplicationError(XledException):
    """Application didn't return successful status code"""

    def __init__(self, *args, **kwargs):
        """Initializes ApplicationError with `response` object."""
        response = kwargs.pop("response", None)
        self.response = response
        super(ApplicationError, self).__init__(*args)


class ValidationError(XledException):
    """Validation of challenge response wasn't successful"""


class AuthenticationError(XledException):
    """Authentication handshake wasn't successful"""


class TokenExpiredError(ApplicationError):
    """Token is no longer valid"""


class HighInterfaceError(XledException):
    """High level interface error"""


class ReceiveTimeout(XledException):
    """Signal that timeout occurred while waiting for data"""


class DiscoverTimeout(XledException):
    """Signal that timeout occurred while discover is looking for a device"""
