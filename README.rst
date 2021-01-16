==================================================================
XLED - unofficial control of Twinkly - Smart Decoration LED lights
==================================================================

XLED is a python library and command line interface (CLI) to control
`Twinkly`_ - Smart Decoration LED lights for Christmas.

Official materials says:

    Twinkly is a LED light device that you can control via smartphone. It
    allows you to play with colouful and animated effects, or create new ones.
    Decoration lights, not suitable for household illumination.

Since its `Kickstarter project`_ in 2016 many products were introduced with
varying properties and features. Most notably products released since September
2019 are identified as Generation II. Older products are since then referred as
Generation I.

Library and CLI are free software available under MIT license.

Documentation for the library can be found on https://xled.readthedocs.io.

Use of the library:

.. code-block:: python

    >>> import xled
    >>> discovered_device = xled.discover.discover()
    >>> discovered_device.name
    'Twinkly_33AAFF'
    >>> control = xled.ControlInterface(discovered_device.ip_address, discovered_device.hw_address)
    >>> control.set_mode('movie')
    >>> control.get_mode()['mode']
    u'movie'
    >>> control.get_device_info()['number_of_led']
    105

Use of the CLI:

.. code-block:: console

    $ xled on
    Looking for any device...
    Working on device: Twinkly_33AAFF
    Turned on.

Unofficial documentation of private protocol and API is `available online`_.


Why?
----

My first Twinkly was 105 LEDs starter light set. That was the latest available
model in 2017: TW105S-EU. As of December 2017 there are only two ways to
control lights: mobile app on Android or iOS or hardware button on the cord.

Android application didn't work as advertised on my Xiaomi Redmi 3S phone. On
first start it connected and disconnected in very fast pace (like every 1-2
seconds) to the hardware. I wasn't able to control anything at all. Later I
wanted to connect it to my local WiFi network. But popup dialog that shouldn't
have appear never did so.

Public API was `promised around Christmas 2016`_ for next season. Later update
from October 2016 it seems `API won't be available any time soon`_:

    API for external control are on our dev check list, we definitely need some
    feedback from the community to understand which could be a proper core set
    to start with.

It turned out that application uses HTTP to control lights. I ended up with
capturing network traffic and `documented this private API`_. In the end I'm
able to configure the device pretty easilly.

As of 2020 Twinkly devices can be controlled by Amazon Alexa and Google
Assistant as well. Mobile application now requires an account to operate lights
even locally. No sign of public API for local devices though. Therefore with my
second device - Twinkly 210 RGB+W Wall I keep improving this library and CLI
documentation to be able to operate my devices locally and not rely on
availability of manufacturer's servers.

References
----------

There are other projects that might be more suitable for your needs:

* `Twinkly integration in Home Assistant`_
* SmartThings:

  * `Twinkly integration in SmartThings by StevenJonSmith`_
  * `Twinkly integration in SmartThings by Dameon87`_

* `TwinklyTree Binding`_ for openHAB
* `Twinkly HomeKit Hub for Mongoose OS`_ using `Twinkly library for Mongoose OS`_
* `TwinklyWPF`_ - .net 5 GUI and API library
* `ioBroker.twinkly`_ - twinkly adapter for ioBroker to communicate with the Twinkly lights
* `Twinkly.vb for HomeSeer`_
* `thingzi-logic-twinkly`_ - Twinkly lights integration for node red
* Python class to interact with generation I device and IDA Pro loader of firmware binary in `Twinkly Twinkly Little Star by F-Secure LABS`_.

Credits
---------

This package was created with Cookiecutter_ and the
`audreyr/cookiecutter-pypackage`_ project template.

.. _`Twinkly`: https://www.twinkly.com/
.. _`Kickstarter project`: https://www.kickstarter.com/projects/twinkly/twinkly-smart-decoration-for-your-christmas
.. _`available online`: https://xled-docs.readthedocs.io
.. _`documented this private API`: https://xled-docs.readthedocs.io
.. _`promised around Christmas 2016`: https://www.kickstarter.com/projects/twinkly/twinkly-smart-decoration-for-your-christmas/comments?cursor=15497325#comment-15497324
.. _`API won't be available any time soon`: https://www.kickstarter.com/projects/twinkly/twinkly-smart-decoration-for-your-christmas/comments?cursor=14619713#comment-14619712
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`documented this private API`: https://xled-docs.readthedocs.io
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`Twinkly library for Mongoose OS`: https://github.com/d4rkmen/twinkly
.. _`Twinkly HomeKit Hub for Mongoose OS`: https://github.com/d4rkmen/twinkly-homekit
.. _`TwinklyWPF`: https://github.com/MarkAlanJones/TwinklyWPF
.. _`Twinkly integration in Home Assistant`: https://www.home-assistant.io/integrations/twinkly/
.. _`ioBroker.twinkly`: https://www.npmjs.com/package/iobroker.twinkly
.. _`Twinkly.vb for HomeSeer`: https://forums.homeseer.com/forum/developer-support/scripts-plug-ins-development-and-libraries/script-plug-in-library/1348314-twinkly-vb-christmas-tree-lights-with-predefined-and-custom-animations
.. _`TwinklyTree Binding`: https://github.com/mvanhulsentop/openhab-addons/tree/twinklytree/bundles/org.openhab.binding.twinklytree
.. _`Twinkly Twinkly Little Star by F-Secure LABS`: https://labs.f-secure.com/blog/twinkly-twinkly-little-star/
.. _`Twinkly integration in SmartThings by StevenJonSmith`: https://github.com/StevenJonSmith/SmartThings
.. _`Twinkly integration in SmartThings by Dameon87`: https://github.com/Dameon87/SmartThings
.. _`thingzi-logic-twinkly`: https://www.npmjs.com/package/thingzi-logic-twinkly

.. image:: https://badges.gitter.im/xled-community/chat.svg
   :alt: Join the chat at https://gitter.im/xled-community/chat
   :target: https://gitter.im/xled-community/chat?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge