# -*- coding: utf-8 -*-
"""
xled.compat
~~~~~~~~~~~

This module handles import compatibility issues between Python 2 and
Python 3.
"""

from __future__ import absolute_import

import sys

# -------
# Pythons
# -------

# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = _ver[0] == 2

#: Python 3.x?
is_py3 = _ver[0] == 3

is_py34 = _ver[:2] == (3, 4)

if is_py2:
    basestring = basestring

elif is_py3:
    basestring = (str, bytes)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    if is_py2 or is_py34:
        # Python < 3.5
        JSONDecodeError = ValueError
    else:
        raise


if is_py2:
    import itertools

    zip = itertools.izip

elif is_py3:
    zip = zip

if is_py2:
    from collections import Mapping  # noqa

elif is_py3:
    from collections.abc import Mapping  # noqa


if is_py2:
    xrange = xrange

elif is_py3:
    xrange = range


if is_py2:
    from monotonic import monotonic

elif is_py3:
    from time import monotonic  # noqa
