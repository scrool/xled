# -*- coding: utf-8 -*-

"""
xled.security
~~~~~~~~~~~~~

This module contains cryptographic functions to encrypt data with shared
secret so it can be transferred over unencrypted connection.

.. seealso::

    :doc:`protocol_details`
        for various operations.
"""

import os
import base64
import hashlib
import itertools
import warnings

import netaddr

from xled.compat import zip, is_py2

if is_py2:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # This import would raise UserWarning on its own
        from cryptography.utils import CryptographyDeprecationWarning

with warnings.catch_warnings():
    if is_py2:
        # Make sure we ignore only CryptographyDeprecationWarning
        warnings.simplefilter("ignore", category=CryptographyDeprecationWarning)

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms


#: Default key to encrypt challenge in login phase
SHARED_KEY_CHALLANGE = b"evenmoresecret!!"

#: Default key to encrypt WiFi password
SHARED_KEY_WIFI = b"supersecretkey!!"

#: Read buffer size for sha1sum
BUFFER_SIZE = 65536


def xor_strings(message, key):
    """
    Apply XOR operation on every corresponding byte

    If key is shorter than message repeats it from the beginning
    until whole message is processed.
    :param bytes message: input message to encrypt
    :param bytes key: encryption key
    :return: encrypted cypher
    :rtype: bytearray
    """
    if is_py2:
        message = bytearray(message)
        key = bytearray(key)
    ciphered = bytearray()
    for m_char, k_char in zip(message, itertools.cycle(key)):
        ciphered.append(m_char ^ k_char)
    return bytes(ciphered)


def derive_key(shared_key, mac_address):
    """
    Derives secret key from shared key and MAC address

    MAC address is repeated to length of key. Then bytes on corresponding
    positions are xor-ed. Finally a string is created.

    :param str shared_key: secret key
    :param str mac_address: MAC address in any format that netaddr.EUI
        recognizes
    :return: derived key
    :rtype: bytes
    """
    mac = netaddr.EUI(mac_address)
    return xor_strings(shared_key, mac.packed)


def rc4(message, key):
    """
    Simple wrapper for RC4 cipher that encrypts message with key
    :param str message: input to encrypt
    :param str key: encryption key
    :return: ciphertext
    :rtype: str
    """
    algorithm = algorithms.ARC4(key)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(message)


def generate_challenge():
    """
    Generates random challenge string

    :rtype: str
    """
    return os.urandom(32)


def make_challenge_response(challenge_message, mac_address, key=SHARED_KEY_CHALLANGE):
    """
    Create challenge response from challenge

    Used in initial login phase of communication with device. Could be
    used to check that device shares same shared secret and implements
    same algorithm to show that it is genuine.

    :param str challenge_message: random message originally sent as
        challenge with login request
    :param str mac_address: MAC address of the remote device in any
        format that netaddr.EUI recognizes
    :param str key: (optional) shared key that device has to know
    :return: hashed ciphertext that must be equal to challenge-response
        in response to login call
    :rtype: str
    """
    secret_key = derive_key(key, mac_address)
    rc4_encoded = rc4(challenge_message, secret_key)
    return hashlib.sha1(rc4_encoded).hexdigest()


def encrypt_wifi_password(password, mac_address, key=SHARED_KEY_WIFI):
    """
    Encrypts password

    This can be used to send password for WiFi in encrypted form over
    unencrypted channel. Ideally only device that knows shared secret
    key and has defined MAC address should be able to decrypt the
    message.

    :param str password: password to encrypt
    :param str mac_address: MAC address of the remote device in any
        format that netaddr.EUI recognizes
    :param str key: (optional) shared key that device has to know
    :return: Base 64 encoded string of ciphertext of input password
    :rtype: str
    """
    if not isinstance(password, bytes):
        password = bytes(password, "utf-8")
    secret_key = derive_key(key, mac_address)
    data = password.ljust(64, b"\x00")
    rc4_encoded = rc4(data, secret_key)
    return base64.b64encode(rc4_encoded)


def sha1sum(fileobj):
    """
    Computes SHA1 from file-like object

    It is up to caller to open file for reading and close it afterwards.

    :param fileobj: file-like object
    :return: SHA1 digest as hexdecimal digits only
    :rtype: str
    """
    sha1 = hashlib.sha1()
    while True:
        data = fileobj.read(BUFFER_SIZE)
        if not data:
            break
        sha1.update(data)
    return sha1.hexdigest()
