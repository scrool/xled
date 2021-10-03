from xled.control import HighControlInterface
from xled.discover import discover
from xled.colorsphere import launch_colorpicker

dev = discover()
ctr = HighControlInterface(dev.ip_address)

launch_colorpicker(ctr, True, True)

