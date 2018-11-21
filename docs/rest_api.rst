=============================
Twinkly private API reference
=============================

Overview
--------

Twinkly API is primary way to get information about the device, configure network and modes of the device. It is a HTTP 1.1 based API sent over TCP port 80.

This API is used by mobile applications. It haven't been made public yet so it may change at any time.


HTTP Responses
--------------

The HTTP response can be used to determine if the request was successful, and if not, whether the request should be retried.

200 Success
    The request was successful.

401 Unauthenticated
    Request requires authentication but authorization failed. Application didn't handle the request.


Application responses
---------------------

The API may return application status as `code` value of JSON. Returned will not necessarily "correspond" with the HTTP status code. For example, a HTTP status code 200 OK returned with an error application code indicates that the request successfully reached the server, but application cannot process the request.

1100
    Ok

1101
    Invalid argument value

1102
    Error

1103
    Error - value too long?

1105
    Invalid argument key


Authentication
--------------

Most API calls require valid authentication token. Except of:

* login
* gestalt
* fw version

If API requires authentication but valid token wasn't passed server returns HTTP status code 401 Unauthenticated and string `Invalid Token.` in the response body.


API calls
---------


Login
-----

Request access token.

HTTP request
````````````

`POST /xled/v1/login`

Parameters
``````````

Parameters as JSON object.

`challenge`
    Random 32 byte string encoded with base64.


Response
````````

The response will be an object.

`authentication_token`
    Access token in format: 8 byte string base64 encoded. First authenticated API with this token must be Verify.

`challenge-response`
    41 byte string ([0-9a-h])

`code`
    Application return code.

`authentication_token_expires_in`: integer. All the time 14400?


Example
````````

Request::

    POST /xled/v1/login HTTP/1.1
    Host: 192.168.4.1
    Content-Type: application/json
    Content-Length: 61

    {"challenge": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="}

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 155
	Content-Type: application/json

	{"authentication_token":"5jPe+ONhwUY=","authentication_token_expires_in":14400,"challenge-response":"8d87f080947e343180da3f411df3997e3e9ae0cc","code":1000}


Verify
------

Verify the token retrieved by Login.

HTTP request
````````````

`POST /xled/v1/verify`

Parameters
``````````

Parameters as JSON object.

`challenge-response`
    (optional) value returned by login request.

Response
````````

The response will be an object.

`code`
    Application return code.


Example
````````

Request::

	POST /xled/v1/verify HTTP/1.1
	Host: 192.168.4.1
	Content-Type: application/json
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Length: 66

	{"challenge-response": "8d87f080947e343180da3f411df3997e3e9ae0cc"}

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 13
	Content-Type: application/json

	{"code":1000}


Device details
--------------

Gets information detailed information about the device.

HTTP request
````````````

`GET /xled/v1/gestalt`

Response
````````

The response will be an object.

`product_name`
	(string) `Twinkly`
`product_version`
	(numeric string), e.g. "2"
`hardware_version`
	(numeric string), e.g. "6"
`flash_size`
	(number), e.g. 16
`led_type`
	(number), e.g. 6
`led_version`
	(string) "1"
`product_code`
	(string), e.g. "TW105SEUP06"
`device_name`
	(string), by default consists of `Twinkly_` prefix and uppercased `hw_id` (see bellow)
`uptime`
	(string) number as a string, e.g. "60"
`hw_id`
	(string), right three bytes of mac address encoded as hexadecimal digits prefixed with 00.
`mac`
	(string) MAC address as six groups of two hexadecimal digits separated by colons (:).
`max_supported_led`
	(number), e.g. 180
`base_leds_number`
	(number), e.g. 105
`number_of_led`
	(number), e.g. 105
`led_profile`
	(string) "RGB"
`frame_rate`
	(number), 25
`movie_capacity`
	(number), e.g. 719
`copyright`
	(string) "LEDWORKS 2017"
`code`
    Application return code.

Example
````````

Request::

	GET /xled/v1/gestalt HTTP/1.1
	Host: 192.168.4.1

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 406
	Content-Type: application/json

	{"product_name":"Twinkly","product_version":"2","hardware_version":"6","flash_size":16,"led_type":6,"led_version":"1","product_code":"TW105SEUP06","device_name":"Twinkly_33AAFF","uptime":"60","hw_id":"0033aaff","mac":"5c:cf:7f:33:aa:ff","max_supported_led":224,"base_leds_number":105,"number_of_led":105,"led_profile":"RGB","frame_rate":25,"movie_capacity":719,"copyright":"LEDWORKS 2017","code":1000}


Get device name
---------------

Gets device name

HTTP request
````````````

`GET /xled/v1/device_name`

Response
````````

The response will be an object.

`name`
	(string) Device name.

`code`
    Application return code.

Example
````````

Request::

	GET /xled/v1/device_name HTTP/1.1
	Host: 192.168.4.1
	X-Auth-Token: 5jPe+ONhwUY=

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 37
	Content-Type: application/json

	{"name":"Twinkly_33AAFF","code":1000}


Set device name
---------------

Sets device name

HTTP request
````````````

`POST /xled/v1/device_name`

Parameters
``````````

Parameters as JSON object.

`name`
	(string) Desired device name. At most 32 characters.

Response
````````

The response will be an object.

`code`
    Application return code. `1103` if too long.


Example
````````

Request::

	POST /xled/v1/device_name HTTP/1.1
	Host: 192.168.4.1
	Content-Type: application/json
	X-Auth-Token: WnqOTdKzTlU=
	Content-Length: 26

	{"name": "Twinkly_33AAFF"}

	GET /xled/v1/device_name HTTP/1.1
	Host: 192.168.4.1
	X-Auth-Token: 5jPe+ONhwUY=

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 37
	Content-Type: application/json

	{"name":"Twinkly_33AAFF","code":1000}


Logout
------

Probably invalidate access token. Doesn't work.

HTTP request
````````````

`POST /xled/v1/logout`

Response
````````

The response will be an object.

`code`
    Application return code.

Example
````````

Request::

	POST /xled/v1/logout HTTP/1.1
	Host: 192.168.4.1
	Content-Type: application/json
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Length: 2

	{}

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 13
	Content-Type: application/json

	{"code":1000}


Set network status
------------------

Sets network mode operation.

HTTP request
````````````

`POST /xled/v1/network/status`

Parameters
``````````

Parameters as JSON object.

`mode`
	(enum) 1 or 2
`station`
	(object) if mode set to 1 this parameter provides additional details.


Station object parameters:

`dhcp`
	(integer) 1

`ssid`
	(string) SSID of a WiFi network

`encpassword`
	(string) encrypted password.

Response
````````

The response will be an object.

`code`
    Application return code.

Example
````````

Request to change network mode to client and connect to SSID "home" with password "Twinkly". Encoded with MAC adress '5C:CF:7F:33:AA:FF'::

	POST /xled/v1/network/status HTTP/1.1
	Host: 192.168.4.1
	Content-Type: application/json
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Length: 150

	{"mode":1,"station":{"ssid":"home","encpassword":"e4XXiiUhg4J1FnJEfUQ0BhIji2HGVk1NHU5vGCHfyclFdX6R8Nd9BSXVKS5nj2FXGU6SWv9CIzztfAvGgTGLUw==","dhcp":1}}

Request to change network mode to AP::

	POST /xled/v1/network/status HTTP/1.1
	Host: 192.168.1.100
	Content-Type: application/json
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Length: 10

	{"mode":2}


Get timer
---------

Gets time when lights should be turned on and time to turn them off.


HTTP request
````````````

`GET /xled/v1/timer`

Response
````````

The response will be an object.

`time_now`
	(integer) current time in seconds after midnight

`time_on`
	(number) time when to turn lights on in seconds after midnight. -1 if not set

`time_off`
	(number) time when to turn lights off in seconds after midnight. -1 if not set


Set timer
---------

Sets time when lights should be turned on and time to turn them off.

HTTP request
````````````

`POST /xled/v1/timer`

Parameters
``````````

Parameters as JSON object.

`time_now`
	(integer) current time in seconds after midnight

`time_on`
	(number) time when to turn lights on in seconds after midnight. -1 if not set

`time_off`
	(number) time when to turn lights off in seconds after midnight. -1 if not set

Example
````````

Request to set current time to 2:00 AM, turn on lights at 1:00 AM and turn off at 4:00 AM::

	POST /xled/v1/timer HTTP/1.1
	Host: 192.168.4.1
	Content-Type: application/json
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Length: 51

	{"time_now": 120, "time_on": 60, "time_off": 240}

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 13
	Content-Type: application/json

	{"code":1000}


Change LED operation mode
-------------------------

Changes LED operation mode.

HTTP request
````````````

`POST /xled/v1/led/mode`

Parameters
``````````

Parameters as JSON object.

`mode`
	(string) mode of operation.

Mode can be one of:

* `off` - turns off lights
* `demo` - starts predefined sequence of effects that are changed after few seconds
* `movie` - plays predefined or uploaded effect
* `rt` - receive effect in real time

Response
````````

The response will be an object.

`code`
    Application return code.

Example
````````

Request::

	POST /xled/v1/led/mode HTTP/1.1
	Host: 192.168.4.1
	Content-Type: application/json
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Length: 15

	{"mode":"demo"}

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 13
	Content-Type: application/json

	{"code":1000}


Upload full movie
-----------------

Effect is received in body of the request with Content-Type application/octet-stream. If mode is `movie` it starts playing this effect.

HTTP request
````````````

`POST /xled/v1/led/movie/full`

Response
````````

The response will be an object.

`code`
    Application return code.
`frames_number`
	(integer) number of received frames



Set LED movie config
--------------------

HTTP request
````````````

`POST /xled/v1/led/movie/config`

Parameters
``````````

Parameters as JSON object.

`frame_delay`
	(integer)

`leds_number`
	(integer) seems to be total number of LEDs to use

`frames_number`
	(integer)

Response
````````

The response will be an object.

`code`
    Application return code.




Get firmware version
--------------------

Note: no authentication needed.

HTTP request
````````````

`GET /xled/v1/fw/version`

Response
````````

The response will be an object.

`code`
    Application return code.

`version`
    (string)

Example
````````

Request::

	GET /xled/v1/fw/version HTTP/1.1
	Host: 192.168.4.1
	Accept: */*

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 33
	Content-Type: application/json

	{"version":"1.99.24","code":1000}


Update firmware
---------------

Probably initiates firmware update.

HTTP request
````````````

`POST /xled/v1/fw/update`

Parameters
``````````

Parameters as JSON object.

`checksum`
	(object)

Checksum object parameters:

`stage0_sha1sum`
	(string) SHA1 digest of first stage

`stage1_sha1sum`
	(string) SHA1 digest of second stage

Response
````````

The response will be an object.

`code`
    Application return code.

Example
````````

Request::

	POST /xled/v1/fw/update HTTP/1.1
	X-Auth-Token: 5jPe+ONhwUY=
	Content-Type: application/json
	Content-Length: 134
	Host: 192.168.4.1

	{"checksum":{"stage0_sha1sum":"1c705292285a1a5b8558f7b39abd22c5550606b5","stage1_sha1sum":"ac691b8d4563dcdbb3f837bf3db2ebf56fe77fbe"}}

Response::

	HTTP/1.1 200 Ok
	Connection: close
	Content-Length: 13
	Content-Type: application/json

	{"code":1000}


Upload first stage of firmware
------------------------------

First stage of firmware is uploaded in body of the request with Content-Type application/octet-stream.

HTTP request
````````````

`POST /xled/v1/fw/0/update`

Response
````````

The response will be an object.

`code`
    Application return code.

`sha1sum`
	SHA1 digest of uploaded firmware.


Upload second stage of firmware
-------------------------------

Second stage of firmware is uploaded in body of the request with Content-Type application/octet-stream.

HTTP request
````````````

`POST /xled/v1/fw/1/update`

Response
````````

The response will be an object.

`code`
    Application return code.

`sha1sum`
	SHA1 digest of uploaded firmware.


Initiate WiFi network scan
--------------------------

HTTP request
````````````

`GET /xled/v1/network/scan`

Response
````````

The response will be an object.

`code`
    Application return code.


Get results of WiFi network scan
--------------------------------

HTTP request
````````````

`GET /xled/v1/network/scan_results`

Response
````````

The response will be an object.

`code`
    Application return code.

`networks`
	Array of objects

Item of networks array is object:

`ssid`
	(string)

`mac`
	(string)

`rssi`
	(number) negative number

`channel`
	(integer)

`enc`
	One of numbers 0 (Open), 1 (WEP), 2 (WPA-PSK), 3 (WPA2-PSK), 4 (WPA-PSK + WPA2-PSK), 5 (WPA2-EAP).


Response seems to correspond with `AT command CWLAP <https://github.com/espressif/ESP8266_AT/wiki/CWLAP>`_.


Set LED driver parameters
-------------------------

HTTP request
````````````
`POST /xled/v1/led/driver_params`


Reset LED
---------

HTTP request
````````````
`GET /xled/v1/led/reset`

Response
````````

The response will be an object.

`code`
    Application return code.
