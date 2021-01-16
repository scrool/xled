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

if is_py2:
    basestring = basestring  # noqa

elif is_py3:
    basestring = (str, bytes)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    if is_py2:
        # Python < 3.5
        JSONDecodeError = ValueError
    else:
        raise


if is_py2:
    import itertools

    zip = itertools.izip

elif is_py3:
    zip = zip  # noqa

if is_py2:
    from collections import Mapping  # noqa

elif is_py3:
    from collections.abc import Mapping  # noqa


if is_py2:
    xrange = xrange  # noqa

elif is_py3:
    xrange = range  # noqa


if is_py2:
    from monotonic import monotonic  # noqa

elif is_py3:
    from time import monotonic  # noqa
