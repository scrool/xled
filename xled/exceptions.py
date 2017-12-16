# -*- coding: utf-8 -*-


class XledException(IOError):
    def __init__(self, *args, **kwargs):
        super(XledException, self).__init__(*args, **kwargs)


class ApplicationError(XledException):
    """Application didn't return successful status code"""
