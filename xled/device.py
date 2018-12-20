# -*- coding: utf-8 -*-

"""
xled.device
~~~~~~~~~~~~~

High level object on single device
"""

from xled.compat import Mapping

from xled.control import HighControlInterface


class Device(Mapping):
    #: These names can be fetched from :py:func:`device_info` property
    DEVICE_INFO = (
        "base_leds_number",
        "copyright",
        "device_name",
        "flash_size",
        "frame_rate",
        "hardware_version",
        "hw_id",
        "led_profile",
        "led_type",
        "led_version",
        "mac",
        "max_supported_led",
        "movie_capacity",
        "number_of_led",
        "product_code",
        "product_name",
        "product_version",
        "rssi",
        "uptime",
        "uuid",
    )
    #: These names can be fetched from :py:func:`network_status` property
    NETWORK_STATUS = ("mode", "station", "ap")
    #: These names can be fetched from :py:func:`timer` property
    TIMER_INFO = ("time_now", "time_off", "time_on")
    #: These names are separate properties
    PROPERTIES = (
        "device_id",
        "on",
        "off",
        "mode",
        "firmware_version",
        "network_mode",
        "host",
    )
    #: These names are properties that can be accessed as items of Mapping.
    ATTRS = PROPERTIES + NETWORK_STATUS + DEVICE_INFO + TIMER_INFO

    def __init__(self, control_interface):
        self._control = control_interface
        self.__device_info = None
        self.__network_status = None

    @classmethod
    def create_device(cls, host, hw_address=None):
        control = HighControlInterface(host, hw_address)
        return cls(control)

    @property
    def host(self):
        return self._control.host

    @property
    def _device_info(self):
        if not self.__device_info:
            info = self._control.get_device_info()
            assert info
            self.__device_info = info
        return self.__device_info

    @property
    def _network_status(self):
        if not self.__network_status:
            status = self._control.get_network_status()
            assert status
            self.__network_status = status
        return self.__network_status

    @property
    def device_info(self):
        info = {}
        for key in self.DEVICE_INFO:
            if key not in self._device_info:
                continue
            info[key] = self._device_info[key]
        return info

    @property
    def network_status(self):
        status = {}
        for key in self.NETWORK_STATUS:
            if key not in self._network_status:
                continue
            status[key] = self._network_status[key]
        return status

    @property
    def timer_info(self):
        timer = self._control.get_formatted_timer()
        return {u"time_now": timer.now, u"time_on": timer.on, u"time_off": timer.off}

    @property
    def device_id(self):
        """
        Device's unique name

        This name is always in device discovery response. It is also initial
        device name after factory reset and SSID if device is in Access Point
        (AP) mode.

        :return: device's unique name
        :rtype: str
        """
        info = self._device_info
        hw_id = info["hw_id"].upper()
        if hw_id.startswith("00"):
            hw_id = hw_id[2:]
        return u"{}_{}".format(info["product_name"], hw_id)

    @property
    def network_mode(self):
        if self._network_status["mode"] == 1:
            return "station"
        elif self._network_status["mode"] == 2:
            return "ap"
        else:
            raise ValueError("Unknown network status")

    @property
    def firmware_version(self):
        fw_version = self._control.firmware_version()
        return fw_version["version"]

    def __getitem__(self, key):
        if key in self.PROPERTIES:
            return getattr(self, key)
        elif key in self.DEVICE_INFO:
            return self.device_info[key]
        elif key in self.NETWORK_STATUS:
            return self.network_status[key]
        elif key in self.TIMER_INFO:
            return self.timer_info[key]

    def __iter__(self):
        return iter(self.ATTRS)

    def __len__(self):
        return len(self.ATTRS)

    def __repr__(self):
        return "<TwinklyDevice [%s]>" % self.id

    def turn_on(self):
        return self._control.turn_on()

    def turn_off(self):
        return self._control.turn_off()

    @property
    def on(self):
        return self._control.is_on()

    @property
    def off(self):
        return not self.on

    @property
    def mode(self):
        return self._control.get_mode()["mode"]

    def set_static_color(self, red, green, blue):
        return self._control.set_static_color(red, green, blue)

    def _set_static_color(self, colors):
        assert len(colors) == 3
        return self.set_static_color(*colors)

    static_color = property(fset=_set_static_color)
