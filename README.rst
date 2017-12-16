==========================
Smart LED Christmas lights
==========================

Unofficial API documentation for Twinkly - Smart Decoration LED lights for
Christmas.

Description of Twinkly on `project page of Kickstarter`:

    Twinkly is a Christmas tree light string, controlled via smartphone:
    "internet of things" meets extraordinary light effects! Created by ledworks

* Free software: MIT license

Documentation is available online at https://xled.readthedocs.io.

Why?
----

I have Twinkly 105 LEDs starter light set. That is latest available model in
2017: TW105S-EU. As of December 2017 there are only two ways to control lights
- mobile app on Android or iOS or hardware button on the cord.

Android application didn't work as advertised on my Xiaomi Redmi 3S phone. On
first start it connected and disconnected in very fast pace (like every 1-2
seconds) to the hardware. I wasn't able to control anything at all. Later I
wanted to connect it to my local WiFi network. But popup dialog that shouldn't
have appear never did so.

Public API was `promised around Christmas 2016` for next season. Later update
from October 2016 it seems `API won't be available any time soon`:

    API for external control are on our dev check list, we definitely need some
    feedback from the community to understand which could be a proper core set
    to start with.

It turned out that application uses HTTP to control lights. I ended up with
capturing network traffic and documented this private API. In the end I'm able
to configure the device pretty easilly.

Credits
---------

This package was created with Cookiecutter_ and the
`audreyr/cookiecutter-pypackage`_ project template.

.. _`project page of Kickstarter`: https://www.kickstarter.com/projects/twinkly/twinkly-smart-decoration-for-your-christmas
.. _`promised around Christmas 2016`: https://www.kickstarter.com/projects/twinkly/twinkly-smart-decoration-for-your-christmas/comments?cursor=15497325#comment-15497324
.. _`API won't be available any time soon`: https://www.kickstarter.com/projects/twinkly/twinkly-smart-decoration-for-your-christmas/comments?cursor=14619713#comment-14619712
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
