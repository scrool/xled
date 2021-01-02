# -*- coding: utf-8 -*-

"""
xled.realtime
~~~~~~~~~~~~~

Functions to support the realtime mode of the device.
"""

from __future__ import absolute_import

import base64
import math
import socket

from xled.control import ControlInterface

#: UDP port to send realtime frames to
REALTIME_UDP_PORT_NUMBER = 7777


class RealtimeChannel(object):
    """
    Main interface to send realtime frames to device.

    :param control: An activated ControlInterface for the device to control
    :param int leds_number: the number of leds in a frame
    :param int bytes_per_led: the number of bytes per led (3 or 4)
    """

    def __init__(self, control, leds_number, bytes_per_led):
        self.control = control
        self.leds_number = leds_number
        self.bytes_per_led = bytes_per_led

    def start_realtime(self):
        self.control.set_mode('rt')

    def send_frame(self, data):
        """
        Sends a realtime frame. Before calling this, start_realtime() must have
        been called.

        :param bytearray data: byte array containing the raw frame data
        :rtype: None
        """
        data_size = self.leds_number*self.bytes_per_led
        assert len(data) == data_size
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            if data_size < 900 and self.leds_number < 256:
                # Send single frame
                packet = bytearray(b'\x01')
                packet.extend(base64.b64decode(self.control.session.access_token))
                packet.extend(bytes([self.leds_number]))
                packet.extend(data)
                sock.sendto(packet, (self.control.host, REALTIME_UDP_PORT_NUMBER))
            else:
                # Send multi frame
                packet_size = 900//self.bytes_per_led
                for i in range(0, math.ceil(data_size/packet_size)):
                    packet_data = data[:(900//self.bytes_per_led)]
                    data = data[(900//self.bytes_per_led):]
                    packet = [ b'\x03', base64.b64decode(self.control.session.access_token),
                        b'\x00\x00', bytes([i])]
                    packet.append(packet_data)
                    sock.sendto(packet, (self.control.host, REALTIME_UDP_PORT_NUMBER))


