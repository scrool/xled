# -*- coding: utf-8 -*-

"""
xled package
~~~~~~~~~~~~

xled is a library to control Twinkly LED lights. Basic usage:

   >>> import xled
   >>> control = xled.HighControlInterface('192.168.4.1')
   >>> control.set_mode('demo')
   >>> control.turn_off()

The other API calls are supported - see `xled.control`. Full documentation
is at <http://xled.readthedocs.io/>.

:copyright: (c) 2017 by Pavol Babinčák
:license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import

# Set default logging handler to avoid "No handler found" warnings.
import logging

from xled.control import ControlInterface, HighControlInterface  # noqa: F401
from xled.device import Device  # noqa: F401
from xled.discover import DiscoveryInterface  # noqa: F401

from .__version__ import __title__, __description__, __version__  # noqa: F401
from .__version__ import __author__, __author_email__  # noqa: F401

try:
    from logging import NullHandler
except ImportError:

    class NullHandler(logging.Handler):
        """Backport of minimal handler that does nothing for Python < 2.7"""

        def emit(self, record):
            pass


logging.getLogger(__name__).addHandler(NullHandler())
