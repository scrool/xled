Authentication
==============

The library uses requests library for RESTful API. Since majority of calls
requires authentication, xled library provides helpers to open authenticated
session or to attach authenticating handler. Here we discuss various approaches
from the most low level one to the highest level one.


ChallengeResponseAuth
---------------------

First approach uses `ChallengeResponseAuth` which could be used like this::

    >>> import requests
    >>>
    >>> from xled.auth import ChallengeResponseAuth
    >>> from xled.response import ApplicationResponse
    >>>
    >>> session = requests.Session()
    >>> session.auth = ChallengeResponseAuth(
    >>>     login_url="/xled/v1/login",
    >>>     verify_url="/xled/v1/verify",
    >>>     hw_address=hw_address,
    >>> )
    >>>
    >>> base_url = "http://{}/xled/v1/".format(hostname)
    >>> url = urljoin(base_url, "summary")
    >>> response = session.get(url)
    >>> ApplicationResponse(response)
    <Response [200]>

Class doesn't have knowledge of login and verification endpoints and therefore
they need to be passed when an object is constructed. Passing hardware address
is optional and if it is not passed, `challenge-response` is not validated,
which is also logged as debug message. To request an API endpoint full URL
needs to be passed every time.


BaseUrlChallengeResponseAuthSession
-----------------------------------

Second approach uses `BaseUrlChallengeResponseAuthSession` whose major
advantage is definition of base URL only once at object creation::

    >>> from xled.auth import BaseUrlChallengeResponseAuthSession
    >>> from xled.response import ApplicationResponse
    >>>
    >>> base_url = "http://{}/xled/v1/".format(hostname)
    >>>
    >>> session = BaseUrlChallengeResponseAuthSession(
    >>>    hw_address=hw_address, base_url=base_url
    >>> )
    >>>
    >>> response = session.get("summary")
    >>> ApplicationResponse(response)
    <Response [200]>

Class have default API endpoints for login and verification so they don't need
to be passed this time. API endpoints can be specified by relative portion of
an URL. Behaviour of the object without hardware address passed is the same as
in previous example.
