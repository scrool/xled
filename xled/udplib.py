# -*- coding: utf-8 -*-

"""
xled.udplib
~~~~~~~~~~~

A Simple UDP class
"""

import socket


DEFAULT_BROADCAST = "255.255.255.255"


class UDP(object):
    handle = None  # Socket for send/recv
    port = 0  # UDP port we work on
    address = ""  # Own address
    broadcast = ""  # Broadcast address

    def __init__(self, port, own_addresses=None, broadcast=DEFAULT_BROADCAST):
        if own_addresses is None:
            local_addrs = socket.gethostbyname_ex(socket.gethostname())[-1]
            own_addresses = []
            for address in local_addrs:
                if not address.startswith("127"):
                    own_addresses.append(address)

        self.own_addresses = own_addresses
        self.broadcast = broadcast
        self.port = port
        # Create UDP socket
        self.handle = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )

        # Ask operating system to let us do broadcasts from socket
        self.handle.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Bind UDP socket to local port so we can receive pings
        self.handle.bind(("", port))

    def send(self, buf):
        self.handle.sendto(buf, 0, (self.broadcast, self.port))

    def recv(self, bufsize):
        while True:
            buf, addrinfo = self.handle.recvfrom(bufsize)
            assert len(addrinfo) == 2
            host, port = addrinfo
            if host in self.own_addresses:
                # print("Received message from myself %s:%d" % addrinfo)
                continue
            if host not in self.own_addresses:
                # print("Found peer %s:%d" % addrinfo)
                break
        return buf, host

    def recv_(self, bufsize):
        buf, addrinfo = self.handle.recvfrom(bufsize)
        assert len(addrinfo) == 2
        host, port = addrinfo
        return buf, host
