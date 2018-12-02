# -*- coding: utf-8 -*-

"""
xled.discover
~~~~~~~~~~~~~

This module contains interface for discovery devices on the network
"""

from __future__ import absolute_import

import logging
import time
import uuid
from threading import Thread

import ipaddress
import zmq
from arpreq import arpreq
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback
from zmq.eventloop.zmqstream import ZMQStream

from xled import udp_client
from xled.compat import basestring, is_py3


# Some time in the future improve logging, e.g.
# https://stackoverflow.com/a/40126988
log = logging.getLogger(__name__)


#: Message to send in ping requests
PING_MESSAGE = b"\x01discover"
#: Default port number to send pings
PING_PORT_NUMBER = 5555
#: Interval in seconds
PING_INTERVAL = 1.0
#: After how many seconds the device is considered offline
PEER_EXPIRY = 5.0


def discover(find_name=None):
    """Wrapper to discover first or specific device

    :param find_name: (optional) Device name to look for. If not set first node
        that responded is returned.
    :return: tuple of hardware address, device name and host name.
    :rtype: tuple
    """
    log.debug("discover()")
    interface = DiscoveryInterface()
    hw_address = device_name = ip_address = None
    while True:
        try:
            response = interface.recv()
        except KeyboardInterrupt:
            interface.stop()
            raise
        assert len(response) > 1
        event = response.pop(0)
        if event == b"JOINED":
            assert len(response) == 3
            hw_address, device_name, ip_address = response
            if find_name is None:
                break
            elif find_name == device_name:
                break
            else:
                print(
                    "Device name {} ({}) joined: {}".format(
                        device_name, hw_address, ip_address
                    )
                )
        elif event == b"ERROR":
            print("Error")
            print("Parameters: {}".format(response))
            interface.stop()
            raise Exception("Error")
        else:
            print("Unknown event: {}".format(event))
            print("Parameters: {}".format(response))
    interface.stop()
    return hw_address, device_name, ip_address


def pipe(ctx):
    """
    Create an inproc PAIR pipe

    Used for communicating between parent and children.

    :param ctx: :class:`zmq.Context` object.
    :return: parent socket, child socket.
    :rtype: tuple
    """
    parent_socket = ctx.socket(zmq.PAIR)
    child_socket = ctx.socket(zmq.PAIR)
    url = "inproc://%s" % uuid.uuid1()
    parent_socket.bind(url)
    child_socket.connect(url)
    return parent_socket, child_socket


class DiscoveryInterface(object):
    """
    Main interface to discover devices on the network

    Starts an UDP ping agent in a background thread automatically after
    initialisation.
    """

    def __init__(self):
        log.debug("DiscoveryInterface(): __init__()")
        self.ctx = zmq.Context()
        p0, p1 = pipe(self.ctx)
        self.agent = InterfaceAgent(self.ctx, p1)
        self.agent_thread = Thread(target=self.agent.start)
        self.agent_thread.start()
        self.pipe = p0
        self._agent_pipe = p1

    def stop(self):
        """
        Stop ping agent and close pipe for communication with callee
        """
        log.debug("Stopping Agent thread.")
        self.agent.stop()
        log.debug("Waiting for Agent thread to join us.")
        self.agent_thread.join()
        log.debug("Closing main thread part of the pipe")
        self.pipe.close()
        log.debug("Closing agent thread part of the pipe")
        self._agent_pipe.close()
        log.debug("Terminating context")
        self.ctx.term()

    def recv(self):
        """
        Receive a message from the interface
        """
        return self.pipe.recv_multipart()


# =====================================================================
# Asynchronous part, works in the background


def decode_discovery_response(data):
    """
    Decodes response for discovery
    """
    log.debug("Received {0!r}".format(data))
    if is_py3:
        if not isinstance(data, bytearray):
            msg = "Data must be bytearray. Was {} instead".format(type(data))
            raise TypeError(msg)
    else:
        if not isinstance(data, basestring):
            msg = "Data must be string. Was {} instead".format(type(data))
            raise TypeError(msg)
    if len(data) < 7:
        msg = "Data must be longer than 7 bytes. " "Was {} instead.".format(len(data))
        raise ValueError(msg)
    if data[4:6] != b"OK":
        msg = "Expected 'OK' in status of data message. " "Was {0!r} instead.".format(
            data[4:6]
        )
        raise ValueError(msg)
    if is_py3:
        tail = 0
    else:
        tail = b"\x00"
    if data[-1] != tail:
        msg = (
            "Expected zero character on the end of message. "
            "Was {0!r} instead.".format(data[-1])
        )
        raise ValueError(msg)

    # First four bytes in reversed order
    ip_address_data = data[3::-1]
    if is_py3:
        ip_address_data = bytes(ip_address_data)
    else:
        # Detect if ipaddress is backport to python 2 - py2-ipaddress
        if (
            hasattr(ipaddress, "bytes")
            and hasattr(ipaddress, "bytearray")
            and ipaddress.bytes == ipaddress.bytearray
        ):
            # py2-ipaddress differs from ipaddress by Google and python 3
            # module:
            #     Since Python 2 has no distinct bytes type, bytearray is used
            #     instead for the "packed" (binary) address representation
            ip_address_data = bytearray(ip_address_data)

    ip_address_obj = ipaddress.ip_address(ip_address_data)
    ip_address_str = str(ip_address_obj)

    device_name = data[6:-1]

    return ip_address_str, device_name


class Peer(object):
    """
    Each object of this class represents one device on the network

    :param hw_address: Hardware (MAC) address of a device.
    :param device_name: Name of the device.
    :param ip_address: IP address of a device.
    """

    def __init__(self, hw_address, device_name, ip_address):
        self.hw_address = hw_address
        self.ip_address = ip_address
        self.device_name = device_name
        self.is_alive()

    def __repr__(self):
        return "Peer({0!r})".format(self.hw_address, self.device_name)

    def is_alive(self):
        """
        Reset the peers expiry time

        Call this method whenever we get any activity from a peer.
        """
        self.expires_at = time.time() + PEER_EXPIRY


class InterfaceAgent(object):
    """
    This structure holds the context for our agent

    This way it can be passed around cleanly to methods that need it.

    :param ctx: :class:`zmq.Context` object.
    :param pipe: Pipe back to the main thread of to pass messages.
    :param loop: (optional) loop to use.
    """

    def __init__(self, ctx, pipe, loop=None):
        self.ctx = ctx
        self.pipe = pipe
        if loop is None:
            loop = IOLoop.instance()
        self.loop = loop
        self.udp = udp_client.UDPClient(PING_PORT_NUMBER, broadcast=True)
        #: Hash of known peers, fast lookup
        self.peers = {}

    def stop(self):
        """
        Stop the loop of agent
        """
        self.loop.add_callback(self.loop.stop)

    def __del__(self):
        try:
            self.loop.add_callback(self.loop.stop)
        except Exception:
            pass

    def start(self):
        """
        Main entry of the thread

        Hooks necessary handlers to send pings, process incoming data and
        mark peers offline if they doesn't respond for long time.
        """
        log.debug("Starting Agent")
        loop = self.loop
        loop.add_handler(self.udp.handle.fileno(), self.handle_beacon, loop.READ)
        stream = ZMQStream(self.pipe, loop)
        stream.on_recv(self.control_message)
        pc = PeriodicCallback(self.send_ping, PING_INTERVAL * 1000)
        pc.start()
        pc = PeriodicCallback(self.reap_peers, PING_INTERVAL * 1000)
        pc.start()
        log.debug("Starting Loop")
        loop.start()
        log.debug("Loop ended")

    def send_ping(self, *args, **kwargs):
        """
        Sends ping message

        Runs periodically.
        """
        log.debug("Sending ping")
        message = PING_MESSAGE
        try:
            self.udp.send(message)
        except Exception:
            log.exception("Failed to send ping")
            self.stop()

    def control_message(self, event):
        """
        Respond to control message from main application thread

        Currently unused.

        :param event: anything.
        """
        print("control message: %s", event)

    def _send_to_pipe_multipart(self, msg_parts):
        """
        Handle errors while sending message to pipe as ERROR message sent to pipe

        Caller should catch use these messages to stop interface thread and thus
        agent as well.

        :param iterable msg_parts: A sequence of objects to send as a multipart message.
        :raises TypeError: after error is caught and ERROR message sent to pipe
        """
        log.debug("Going to send %r.", msg_parts)
        try:
            self.pipe.send_multipart(msg_parts)
        except TypeError as err:
            log.error("Failed to send multipart message to pipe: %s", err)
            self.pipe.send_multipart(
                [b"ERROR", b"Failed to send a message to main thread."]
            )
            raise
        finally:
            self.stop()

    def handle_beacon(self, fd, event):
        """
        Reads response from nodes

        Creates :class:`Peer` objects and tracks them in `self.peers`. Finally
        sends messages through pipe to main application thread.

        :param fd: not used
        :param event: not used
        """
        log.debug("Waiting for a beacon.")
        data, host = self.udp.recv(64)
        if data == PING_MESSAGE:
            log.debug("Ignoring ping message received from network from %s.", host)
            return
        log.debug("Received a beacon from %s.", host)
        ip_address, device_name = decode_discovery_response(data)
        # if host != ip_address:
        # print("Host {} != ip_address {}".format(host, ip_address))
        log.debug("Getting hardware address of %s.", ip_address)
        hw_address = arpreq(ip_address)
        if hw_address is None:
            log.error("Unable to get HW adress of %s.", ip_address)
            msg_parts = [b"ERROR", device_name, ip_address]
            try:
                self._send_to_pipe_multipart(msg_parts)
            except Exception:
                return
        # print("Host {} has MAC address {}".format(ip_address, hw_address))
        if hw_address in self.peers:
            log.debug("Peer %s seen before.", hw_address)
            self.peers[hw_address].is_alive()
            if device_name != self.peers[hw_address].device_name:
                old_device_name = self.peers[hw_address].device_name
                self.peers[hw_address].device_name = device_name
                msg_parts = [b"RENAMED", hw_address, old_device_name, device_name]
                try:
                    self._send_to_pipe_multipart(msg_parts)
                except Exception:
                    return
            if ip_address != self.peers[hw_address].ip_address:
                old_ip_address = self.peers[hw_address].ip_address
                self.peers[hw_address].ip_address = ip_address
                msg_parts = [b"ADDRESS_CHANGED", hw_address, old_ip_address, ip_address]
                try:
                    self._send_to_pipe_multipart(msg_parts)
                except Exception:
                    return
        else:
            log.debug("Never seen %s before.", hw_address)
            self.peers[hw_address] = Peer(hw_address, device_name, ip_address)
            msg_parts = [b"JOINED", hw_address, device_name, ip_address]
            try:
                self._send_to_pipe_multipart(msg_parts)
            except Exception:
                return

    def reap_peers(self):
        """
        Removes peers whose activity wasn't seen for a long time

        Called periodically. Sends messages through pipe to main application
        thread.
        """
        now = time.time()
        for peer in list(self.peers.values()):
            if peer.expires_at < now:
                log.debug("reaping %s", peer.hw_address, peer.expires_at, now)
                self.peers.pop(peer.hw_address)
                msg_parts = [b"LEFT", peer.hw_address]
                try:
                    self._send_to_pipe_multipart(msg_parts)
                except Exception:
                    return
