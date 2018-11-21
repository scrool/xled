# -*- coding: utf-8 -*-

"""
xled.util
~~~~~~~~~~~~~

Miscellaneous utility functions.
"""

from __future__ import absolute_import

import datetime


def seconds_after_midnight():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (now - midnight).seconds


def date_from_seconds_after_midnight(seconds):
    now = datetime.datetime.now()
    then = now + datetime.timedelta(seconds=seconds)
    return then


def seconds_after_midnight_from_time(hours, minutes):
    return hours * 60 * 60 + minutes * 60
