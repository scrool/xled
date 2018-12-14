# -*- coding: utf-8 -*-

"""
xled.udp_client
~~~~~~~~~~~~~~~

A Simple UDP class
"""

import socket
from xled.exceptions import ReceiveTimeout


DEFAULT_BROADCAST = "255.255.255.255"


class UDPClient(object):
    """
    Creates simple UDP client

    Object can be used either to send to broadcast or unicast address.

    :param int port: destination port to connect to and from which received
        packets will be read.
    :param destination_host: unicast IP address to send packets to. If
        broadcast parameter is set to True and this parameter is left to None
        :py:const:`DEFAULT_BROADCAST` is used automatically.
    :type destination_host: str or None
    :param bool broadcast: use broadcast for a socket
    """

    def __init__(
        self, port, destination_host=None, broadcast=False, receive_timeout=None
    ):
        self.port = port
        self.broadcast = broadcast
        self.receive_timeout = receive_timeout
        if destination_host:
            self.destination_host = destination_host
        elif broadcast:
            self.destination_host = DEFAULT_BROADCAST
        else:
            raise ValueError("Destination host cannot be None if broadcast is not set.")

        self._own_addresses = None
        self._handle = None

    @property
    def handle(self):
        """
        Socket handler for send/recv
        """
        if self._handle is None:
            _handle = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )
            if self.broadcast:
                _handle.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            _handle.bind(("", self.port))
            if self.receive_timeout:
                _handle.settimeout(self.receive_timeout)
            self._handle = _handle
            assert self._handle is not None
        return self._handle

    @property
    def own_addresses(self):
        """
        List of own addresses

        Used by :py:func:`recv`.
        """
        if self._own_addresses is None:
            local_addrs = socket.gethostbyname_ex(socket.gethostname())[-1]
            own_addresses = []
            for address in local_addrs:
                if not address.startswith("127"):
                    own_addresses.append(address)
            self._own_addresses = own_addresses
            assert self._own_addresses is not None
        return self._own_addresses

    def close(self):
        """Closes socket handler"""
        self.handle.close()

    def send(self, message):
        """
        Send a message

        :param str message: message to send
        :return: number of bytes sent
        :rtype: int
        """
        return self.handle.sendto(message, 0, (self.destination_host, self.port))

    def recv(self, bufsize):
        """
        Blocks until message is received

        Skips messages received from any address stored in
        :py:attr:`own_addresses`.

        :param int bufsize: the maximum amount of data to be received at once
        :return: received message, sender address
        :rtype: tuple
        """
        while True:
            try:
                buf, addrinfo = self.handle.recvfrom(bufsize)
            except socket.timeout:
                raise ReceiveTimeout
                continue
            assert len(addrinfo) == 2
            host, port = addrinfo
            if host in self.own_addresses:
                # print("Received message from myself %s:%d" % addrinfo)
                continue
            if host not in self.own_addresses:
                # print("Found peer %s:%d" % addrinfo)
                break
        return buf, host
