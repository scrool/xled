=======
History
=======

0.7.0 (2021-11-28)
------------------
* Major changes:

  * Add realtime UDP protocol including unit tests
  * Add several missing rest calls in ControlInterface
  * Unit test all methods in ControlInterface

* Other bugfixes and improvements:

  * Provide a short guide how to install packages from PyPI
  * Provide `python_requires` in setup.py
  * Add project URLs to metadata
  * Corrected import of security, and removed some old comments
  * Make encrypt_wifi_password work also with python3
  * More flexible parameters to set_mqtt_config
  * Enable options in set_network_mode_ap and _station
  * Enable relative values in set_brightness
  * Make firmware_update compatible with Generation II
  * Fix error in `python setup.py install` (fix #82)
  * Use generic Exception in discover module
  * On Python 2.7 ignore VCR deprecation warning
  * On Python 2.7 ignore cryptography deprecation warning
  * Fix dependencies for python 2.7
  * Don't debug log reapped devices
  * Time format as hardcoded value instead of locale specific
  * Raise an exception with a error message firmware update failed
  * Get MAC address from gestalt API call
  * Always UTF-8 decode response from JOINED event in discovery
  * Log instead of print in discovery interface and return on unknown event
  * If hw_address wasn't possible to resolve don't use None as a peer
  * Configure all loggers used by CLI with cli_log.basic_config()
  * Make response assertions less strict
  * Reformat setup py so tox tests pass

* Documentation updates:

  * Update example in README to use reflect change in API
  * Add Gitter badge
  * Update of xled and xled-docs should be done hand in hand
  * Remove Enhancement section from Contributing as there is no such thing
  * Write down support for OS, devices, python and guide to CLI
  * Rewrite README file
  * Fix documentation for set_led_movie_config

* Changes in CI/CD:

  * Run linters as GitHub action
  * Use generic python3 in black pre-commit config
  * Configure pytest to collect tests only from tests/
  * Use GitHub action for PyPI publish
  * Update URL for CI from Travis to GitHub actions
  * One more place to update supported python versions
  * Make Travis environment python again
  * Remove non-deploy section from travis.yml
  * Fix typo in travis.yml dep install
  * Ignore Flake8 error on Sphinx configuration file
  * Run pytest directly from Tox
  * Add bug report template for GitHub issues and reference it
  * Switch to token authentication for deployment to pypi through Travis

* Changes in dependencies and python versions:

  * Add 3.10 to supported Python versions
  * Update coverage from 4.4.2 to 5.5
  * Update pip from 20.2.3 to 21.1
  * Update travis.yaml: remove python 3.5 and add 3.8 and 3.9
  * Add 3.9 to supported Python versions
  * Drop Python 3.5 support
  * Drop compatibility code for Python version 3.4
  * Add Python 3.8 as a supported language
  * Update pip from 19.0.3 to 20.2.3
  * Update sphinx from 1.6.5 to 3.0.4

0.6.1 (2020-01-17)
------------------
* Make tests with tox pass again so release can be automatically deployed:

  * Add Black reformatter to tox linter envs
  * Tox config: new linters env to run Flake8
  * Tox config update: Flake8 against tests/ and setup.py as well
  * Make xled.compat pass Flake8 for F821 undefined names
  * Refactor beacon processing of seen/new peer into separate methods
  * Reformat test_control test with black
  * Make tox install test-only requires
  * Use conditional deployment to pypi with travis only from master

0.6.0 (2020-01-15)
------------------
* Drop support for python 3.4
* Explicitly specify Linux as only operating system
* Automatically refresh token if expired
* Add brightness management
* Check response is OK before trying to decode JSON from body
* Use id instead of name in discovery
* Device class representing the device
* Get network status in control interface
* Use response from alive device to check if we reached discover timeout
* Provide generator xdiscover() to return all or specific devices
* Support timeout for discovery
* When agent stops stop ping task and processing responses
* Provide close() for UDPClient and use it on DiscoveryInterface.stop()
* Do not continue receiving more data if UDP recv timeouts
* Other bugfixes and improvements:

  * Fix assertions
  * Expose HighControlInterface on package level
  * If ApplicationError is raised, store value of response attribute
  * Allow disable/enable of brightness without value change
  * Update wheel from 0.30.0 to 0.33.1
  * Update pip from 9.0.1 to 19.0.3
  * Add python 3.6 and 3.7 to Travis config

0.5.0 (2018-12-09)
------------------

* CLI to update firmware
* Example of library call and CLI usage
* Option to select device by hostname in CLI and ping in discovery
* New HighControlInterface() to aggregate and abstract low-level calls
* CLI and HighControlInterface way to set static single color
* Other bugfixes and improvements:

  * Fix typo in CLI error message
  * Print message before discovery on CLI
  * Refactor: join consecutive strings on same line
  * Print better message after device has been discovered over CLI
  * Regenerate documentation index of a package
  * Fix typo in control.set_mode() documentation
  * Return named tuple in discover.discover()
  * Use discovery and named tuple in example of library use
  * Do not assert return value in ControlInterface.set_led_movie_full()
  * Return ApplicationResponse for ControlInterface.set_led_movie_config()
  * Return ApplicationResponse for control.ControlInterface.led_reset()
  * Remove unneeded debug message from DiscoveryInterface.__init__()

0.4.0 (2018-12-03)
------------------

* Support Python 3.6 and 3.7 including tests and documentation
* Python 3 support with pyzmq >= 17.0 and Tornado 5
* Remove redundant udplib
* Other Python 3 compatibility:

  * In Python 3+ import Mapping from collections.abc
  * Python 3 compatible encoding of discovered IP and HW address and name
  * Make xled.security.xor_strings() compatible with Python 2 and 3
  * Treat PING_MESSAGE as bytes to simplify handling Python 2 and 3

* Other bugfixes and improvements:

  * Remove mention of PyPy from docs as it wasn't ever tested on it
  * Improve robustness with sending messages from agent to interface
  * Escape display of binary challenge in debug log of xled.auth
  * Ignore (usually own) PING_MESSAGE on network when handling responses

0.3.1 (2018-11-27)
------------------

* Update changelog for version 0.3.0
* Update description in setup.py to refer to CLI
* Fix JSON payload sent to server for firmware update.

0.3.0 (2018-11-27)
------------------

* CLI interface
* Discovery interface - currently works only on Python 2
* Add support for API led/movie/full and corresponding CLI upload-movie
* New Authentication mechanism - use session
* Rename authentication module from long challenge_response_auth to auth
* Change interface of ApplicationResponse to collections.Mapping
* Python files reformatted with Black
* Other bugfixes and improvements:

  * Really show ApplicationResponse status in repr() when available
  * Catch JSONDecodeError in Python 3.5+ in ApplicationResponse
  * New shortcut method ok() of ApplicationResponse
  * Make ApplicationResponse's attribute status_code @property
  * Improve error reporting during parsing of ApplicationResponse
  * If repr() of ApplicationResponse is called parse response first
  * Check status of underlying requests' Response if requested
  * Accept requests' response as attribute to class ApplicationResponse
  * Move generate_challenge to security module
  * Unit tests for control interface
  * Run unit tests on supported python versions with tox and Travis
  * Configuration for pre-commit-hooks
  * Initial pyup configuration
  * Don't run Tox on Travis on Python 3.3
  * Update coverage

0.2.1 (2018-01-02)
------------------

* Add missing MANIFEST.in
* Configure Travis for automatic deployment to PyPI

0.2.0 (2018-01-02)
------------------

* First Python control interface.

0.1.0 (2017-12-17)
------------------

* Low level control interface.
