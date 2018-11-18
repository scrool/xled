Twinkly private protocol details
================================

This page describes hardware, modes of operation and some private procols or algorithms used by Twinkly application.


My hardware
-----------

I have model TW105S-EU. That's 105 RGB LED model from 2017.

Hardware consists of two circuit boards:

- Module ESP-01 with microcontroller ESP8266 by Espressif Systems.
- Custom-made LED driver module

API exposes these details:

- Product version: 2
- Hardware version: 6
- Flash size: 16
- LED Type: 6
- LED Version: 1
- Product code: TW105SEUP06


Firmware info
-------------
Firmware can be upgraded over the network. I have actually used strings from the firmware to find secret keys, encryption algorithms and some API calls that I haven't seen on the network. It consists of two files. First image format is according to https://github.com/espressif/esptool in version: 1.

I have seen these two versions only so this page describes its behaviour:

- 1.99.20
- 1.99.24


Device name
-----------

Device name is used to announce SSID if it operates in AP mode, or to select device in the application. By default consists of prefix **Twinkly_** and uppercased unique identifier derived from MAC address. It can be read or changed by API.


Modes of network operation
--------------------------

Hardware works in two network modes:

- Access Point (AP)
- Station (STA)

AP mode is default - after factory reset. Broadcasts SSID made from `device name`_. Server uses static IP address 192.168.4.1 and operates in network 192.168.4.0/24. Provides DHCP server for any device it joins the network.

To switch to STA mode hardware needs to be configured with SSID network to connect to and encrypted password. Rest is simple API call through TCP port 80 (HTTP).

Switch from STA mode back to AP mode is as easy as another API call.

http://41j.com/blog/2015/01/esp8266-access-mode-notes/


WiFi password encryption
------------------------

1. Generate encryption key

   1. Use secret key: **supersecretkey!!**
   2. get byte representation of MAC adress of a server and repeat it to length of the secret key
   3. xor these two values

2. Encrypt

   1. Use password to access WiFi and pad it with zero bytes to length 64 bytes.
   2. Use rc4 to encrypt padded password with the *encryption key*

3. Encode

   Base64 encode encrypted string.


Discovery
---------

This seems to be used to find all Twinkly devices on the network.

1. Application sends UDP broadcast to port 5555 with message **\\x01discover** (first character is byte with hex representation 0x01).
2. Server responds back with following message:

   - first four bytes are octets of IP address written in reverse - first byte is last octet of the IP adress, second second to last, ...

   - fifth and sixth byte forms string "OK"

   - rest is string representing `device name`_ padded with zero byte.


Get and verify authentication token
-----------------------------------

Application uses TCP port 80 to get and verify authentication token. It is later used for some calls that require it.

1. Application generates challenge and sends it as part of login request.
2. Among other data server responds with authentication token
3. Application uses authentication_token in header of request to verify.

Only after this handshake authenticationa token can be used in other calls. Most of them require it.


Verification of challenge-response
----------------------------------

As part of login process server sends not only authentication token but also challenge-response. Application may verify if it shares secret with server - maybe if it is genuine Twinkly device with following algorightm:

1. Generate encryption key

   1. Use secret key: **evenmoresecret!!**
   2. get byte representation of MAC adress of a server and repeat it to length of the secret key
   3. xor these two values

2. Encrypt - use rc4 to encrypt challenge with the key

3. Generate hash digest - encrypted data with SHA1

4. Compare - hash digest must be same as challenge-response from server


Firmware update
---------------

Update sequence follows:

1. application sends first file to endpoint 0 over HTTP
2. server returns sha1sum of received file
3. application sends second file to endpoint 1 over HTTP
4. server returns sha1sum of received file
5. application calls update API with sha1sum of each stages.


LED effect operating modes
--------------------------

Hardware can operate in one of following modes:

- off - turns off lights
- demo - starts predefined sequence of effects that are changed after few seconds
- movie - plays last uploaded effect
- rt - receive effect in real time

First two are set just by API call.


Upload full movie LED effect
----------------------------

1. Application calls API to switch mode to movie
2. Application calls API movie/full with file sent as part of the request
3. Application calls config movie call with additional parameters of the movie


Movie file format
-----------------

LED effect is called **movie**. It consists of **frames**. Each frame defines colour of each LED.

Movie file format is simple sequence of bytes. Three bytes in a row represent intensity of *red*, *green* and *blue* in this order. Each frame is defined just with number of LEDs times three. Frames don't have any separator. Definition of each frame starts from LED closer to LED driver/adapter.


Real time LED operating mode
----------------------------

1. Application calls HTTP API to switch mode to rt
2. Then UDP packets are sent to a port 7777 of device. *Each packet represents single frame* that is immediately displayed. See bellow for format of the packets.
3. After some time without any UDP packets device switches back to movie mode.


Real time LED UDP packet format
-------------------------------

Before packets are sent to a device application needs to login and verify authentication token. See above.

Each UDP has header:

* 1 byte *\\x01* (byte with hex representation 0x01)
* 8 bytes Base 64 decoded authentication token
* 1 byte number of LED definitions in the frame

Then follows body of the frame similarly to movie file format - three bytes for each LED.

For my 105 LED each packet is 325 bytes long.


Scan for WiFi networks
----------------------

Hardware can be used to scan for available WiFi networks and return some information about them. I haven't seen this call done by the application so I guess it can be used to find available channels or so.

1. Call network scan API
2. Wait a little bit
3. Call network results API
