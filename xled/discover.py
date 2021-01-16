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
import collections
import requests

from threading import Thread

import ipaddress
import zmq
import tornado.log
from tornado.ioloop import IOLoop, PeriodicCallback
from zmq.eventloop.zmqstream import ZMQStream

from xled import udp_client
from xled.compat import basestring, is_py3, monotonic
from xled.exceptions import ReceiveTimeout, DiscoverTimeout

if is_py3:
    import asyncio
    import tornado.platform.asyncio


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


def xdiscover(find_id=None, destination_host=None, timeout=None):
    """Generator discover all devices or device of specific id

    Device can be specified either by id or by host.

    :param str find_id: (optional) Device id to look for. If not set first node
        that responded is returned.
    :param str destination_host: (optional) Ping selected node only.
    :param float timeout: (optional) Number of seconds until discovery timeouts.
    :return: namedtuple of hardware address, device id and host name.
    :rtype: namedtuple
    :raises DiscoverTimeout: timeout exceeded while waiting for a device
    """
    assert not (find_id and destination_host)
    receive_timeout = None
    if timeout:
        receive_timeout = timeout / 2
    hw_address = device_id = ip_address = None
    start = monotonic()
    with DiscoveryInterface(
        destination_host, receive_timeout=receive_timeout
    ) as interface:
        while True:
            try:
                response = interface.recv()
            except KeyboardInterrupt:
                raise
            assert len(response) > 0
            event = response.pop(0)
            if event == b"JOINED":
                assert len(response) == 3
                hw_address, device_id, ip_address = response
                if isinstance(hw_address, bytes):
                    hw_address = hw_address.decode("utf-8")
                if isinstance(device_id, bytes):
                    device_id = device_id.decode("utf-8")
                if isinstance(ip_address, bytes):
                    ip_address = ip_address.decode("utf-8")
                if find_id is None or find_id == device_id:
                    DiscoveredDevice = collections.namedtuple(
                        "DiscoveredDevice", ["hw_address", "id", "ip_address"]
                    )
                    yield DiscoveredDevice(hw_address, device_id, ip_address)
                    if find_id == device_id:
                        return
                else:
                    log.debug(
                        "Device id {} ({}) joined: {}".format(
                            device_id, hw_address, ip_address
                        )
                    )
                if timeout and (monotonic() - start) > timeout:
                    raise DiscoverTimeout()
            elif event == b"ERROR":
                log.error(
                    "Received error from discovery. Parameters: {}".format(response)
                )
                raise Exception("Error")
            elif event == b"RECEIVE_TIMEOUT":
                assert timeout
                if monotonic() - start > timeout:
                    raise DiscoverTimeout()
                else:
                    continue
            elif event == b"ALIVE":
                if timeout and (monotonic() - start) > timeout:
                    raise DiscoverTimeout()
            else:
                log.error("Unknown event: {}".format(event))
                log.error("Parameters: {}".format(response))
                raise Exception("Unknown event")


def discover(find_id=None, destination_host=None, timeout=None):
    """Wrapper of :py:func:`xdiscover` to return first entry"""
    return next(
        xdiscover(find_id=find_id, destination_host=destination_host, timeout=timeout)
    )


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

    def __init__(self, destination_host=None, receive_timeout=None):
        # As of 15.0, pyzmq supports asyncio. Asyncio requries Python 3.
        if is_py3:
            asyncio.set_event_loop_policy(
                tornado.platform.asyncio.AnyThreadEventLoopPolicy()
            )
        self.ctx = zmq.Context()
        p0, p1 = pipe(self.ctx)
        self.agent = InterfaceAgent(
            self.ctx, p1, destination_host, receive_timeout=receive_timeout
        )
        self.agent_thread = Thread(target=self.agent.start)
        self.agent_thread.start()
        self.pipe = p0
        self._agent_pipe = p1

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

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
        if isinstance(data, bytes):
            data = bytearray(data)
        if not isinstance(data, bytearray):
            msg = "Data must be bytearray. Was {} instead".format(type(data))
            raise TypeError(msg)
    else:
        if not isinstance(data, basestring):
            msg = "Data must be string. Was {} instead".format(type(data))
            raise TypeError(msg)
    if len(data) < 7:
        msg = "Data must be longer than 7 bytes. Was {} instead.".format(len(data))
        raise ValueError(msg)
    if data[4:6] != b"OK":
        msg = "Expected 'OK' in status of data message. Was {0!r} instead.".format(
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
    ip_address_exploded = ip_address_obj.exploded
    if is_py3:
        if not isinstance(ip_address_exploded, bytes):
            ip_address_exploded = bytes(ip_address_exploded, "utf-8")
    else:
        ip_address_exploded = ip_address_exploded.encode("utf-8")

    device_id = data[6:-1]
    if is_py3:
        device_id = bytes(device_id)
    else:
        device_id = device_id.encode("utf-8")

    return ip_address_exploded, device_id


class Peer(object):
    """
    Each object of this class represents one device on the network

    :param hw_address: Hardware (MAC) address of a device.
    :param device_id: Id of the device.
    :param ip_address: IP address of a device.
    """

    def __init__(self, hw_address, device_id, ip_address):
        self.hw_address = hw_address
        self.ip_address = ip_address
        self.device_id = device_id
        self.is_alive()

    def __repr__(self):
        return "Peer({0!r}) device_id({1!r})".format(self.hw_address, self.device_id)

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

    def __init__(
        self, ctx, pipe, loop=None, destination_host=None, receive_timeout=None
    ):
        self.ctx = ctx
        self.pipe = pipe
        if loop is None:
            loop = IOLoop.instance()
        self.loop = loop
        if destination_host:
            udp = udp_client.UDPClient(
                PING_PORT_NUMBER,
                destination_host=destination_host,
                receive_timeout=receive_timeout,
            )
        else:
            udp = udp_client.UDPClient(
                PING_PORT_NUMBER, broadcast=True, receive_timeout=receive_timeout
            )
        self.udp = udp
        #: Hash of known peers, fast lookup
        self.peers = {}

    def _close(self):
        log.debug("Stopping periodic ping.")
        self.periodic_ping.stop()
        log.debug("Removing beacon handler.")
        self.loop.remove_handler(self.udp.handle.fileno())
        log.debug("Closing UDP client.")
        self.loop.add_callback(self.udp.close)
        log.debug("Stopping loop from agent")
        self.loop.add_callback(self.loop.stop)

    def stop(self):
        """
        Stop the loop of agent
        """
        self._close()

    def __del__(self):
        try:
            self._close()
        except Exception:
            pass

    def start(self):
        """
        Main entry of the thread

        Hooks necessary handlers to send pings, process incoming data and
        mark peers offline if they doesn't respond for long time.
        """
        log.debug("Starting Agent")
        self.loop = tornado.ioloop.IOLoop.current()
        self.loop.add_handler(
            self.udp.handle.fileno(), self.handle_beacon, self.loop.READ
        )
        stream = ZMQStream(self.pipe, self.loop)
        stream.on_recv(self.control_message)
        self.periodic_ping = PeriodicCallback(self.send_ping, PING_INTERVAL * 1000)
        self.periodic_ping.start()
        self.periodic_reap_peers = PeriodicCallback(
            self.reap_peers, PING_INTERVAL * 1000
        )
        self.periodic_reap_peers.start()
        log.debug("Starting Loop")
        self.loop.start()
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
        log.debug("control message: %s", event)

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
            self.stop()
            raise

    def _next_packet(self):
        """
        Reads packet from nodes

        :return: tuple received data, hostname
        """
        while True:
            data, host = self.udp.recv(64)
            return data, host

    def get_mac_address(self, ip_address):
        """
        Gets the MAC address of the device at ip_address.

        :param ip_address: The IP address or hostname to the device
        :return: The MAC address, or None in case of failure
        """
        ip = ip_address.decode("utf-8")

        base_url = "http://{}/xled/v1/gestalt".format(ip)
        r = requests.get(base_url)
        if r.status_code != 200:
            log.error(
                "Failure getting MAC address from device at {}. Not a Twinkly?".format(
                    ip
                )
            )
            return None

        try:
            hw_address = r.json().get("mac").encode("utf-8")
            return hw_address
        except Exception:
            return None

    def handle_beacon(self, fd, event):
        """
        Reads response from nodes

        Creates :class:`Peer` objects and tracks them in `self.peers`. Finally
        sends messages through pipe to main application thread.

        :param fd: not used
        :param event: not used
        """
        log.debug("Waiting for a beacon.")
        try:
            data, host = self._next_packet()
        except ReceiveTimeout:
            msg_parts = [b"RECEIVE_TIMEOUT"]
            try:
                self._send_to_pipe_multipart(msg_parts)
            except Exception:
                return
            return
        if data == PING_MESSAGE:
            log.debug("Ignoring ping message received from network from %s.", host)
            return
        log.debug("Received a beacon from %s.", host)
        ip_address, device_id = decode_discovery_response(data)
        # if host != ip_address:
        # print("Host {} != ip_address {}".format(host, ip_address))
        log.debug("Getting hardware address of %s.", ip_address)
        hw_address = self.get_mac_address(ip_address)
        if hw_address is None:
            log.error("Unable to get HW adress of %s.", ip_address)
            msg_parts = [b"ERROR", device_id, ip_address]
            try:
                self._send_to_pipe_multipart(msg_parts)
            except Exception:
                return
            return
        # print("Host {} has MAC address {}".format(ip_address, hw_address))
        if hw_address in self.peers:
            log.debug("Peer %s seen before.", hw_address)
            return self.process_seen_peer(hw_address, device_id, ip_address)
        else:
            log.debug("Never seen %s before.", hw_address)
            return self.process_new_peer(hw_address, device_id, ip_address)

    def process_seen_peer(self, hw_address, device_id, ip_address):
        """
        Updates seen peer's info and sends out status message

        This is called when we receive a message from a peer that we track as
        seen peers. Updates expiry time for a peer and sends out ALIVE message.
        If device ID or IP address changed updates peer's info and sends out
        message RENAMED or ADDRESS_CHANGED messages respectively.

        :param str hw_address: HW address of a device from which we have
                               received a beacon. Must exist in list of peers.
        :param str device_id: device ID decoded from a beacon
        :param str ip_address: IP address decoded from a beacon
        """
        assert hw_address in self.peers
        self.peers[hw_address].is_alive()
        if device_id != self.peers[hw_address].device_id:
            old_device_id = self.peers[hw_address].device_id
            self.peers[hw_address].device_id = device_id
            msg_parts = [b"RENAMED", hw_address, old_device_id, device_id]
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
        msg_parts = [b"ALIVE", hw_address, device_id, ip_address]
        try:
            self._send_to_pipe_multipart(msg_parts)
        except Exception:
            return

    def process_new_peer(self, hw_address, device_id, ip_address):
        """
        Adds new peer and sends out status message

        This is called when we receive a message from HW address we don't have
        in a list of peers. Adds peer info in a list of peers sends out message
        JOINED message.

        :param str hw_address: HW address of a device from which we have
                               received a beacon. Must not exist in list of
                               peers.
        :param str device_id: device ID decoded from a beacon
        :param str ip_address: IP address decoded from a beacon
        """
        assert hw_address not in self.peers
        self.peers[hw_address] = Peer(hw_address, device_id, ip_address)
        msg_parts = [b"JOINED", hw_address, device_id, ip_address]
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
                self.peers.pop(peer.hw_address)
                msg_parts = [b"LEFT", peer.hw_address]
                try:
                    self._send_to_pipe_multipart(msg_parts)
                except Exception:
                    return
