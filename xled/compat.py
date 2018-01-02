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
    basestring = basestring

elif is_py3:
    basestring = (str, bytes)
