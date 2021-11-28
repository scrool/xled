#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import sys

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

#: Common requirements
requirements = [
    "click-log",
    "cryptography",
    "requests-toolbelt",
    "requests",
]

#: Python 2 requirements
requirements_py2 = [
    "ipaddress",
    "monotonic",
    "tornado>=5.0.0,<=5.1.1",
    "pyzmq>=17,<20.0.0",
    "Click>=6.0,<8.0",
    "netaddr<=0.7.19",  # Dependencies zipp and importlib-resources no longer supports Python 2.7
]

#: Python 3 requirements
requirements_py3 = [
    "tornado>=5.0.0",
    "pyzmq>=17",
    "Click>=6.0",
    "netaddr",
]

tests_requirements = ["vcrpy-unittest"]

if sys.version_info > (3, 3):
    requirements.extend(requirements_py3)
else:
    requirements.extend(requirements_py2)

setup(
    name="xled",
    # bumpversion v0.5.3 doesn't handle version string in double quotes
    # correctly so prevent Black to format it:
    # fmt: off
    version='0.7.0',
    # fmt: on
    description=(
        "Python library and command line interface to control "
        "Twinkly - Smart Decoration LED lights for Christmas."
    ),
    long_description=readme + "\n\n" + history,
    author="Pavol Babinčák",
    author_email="scroolik@gmail.com",
    url="https://github.com/scrool/xled",
    packages=find_packages(include=["xled"]),
    entry_points={"console_scripts": ["xled=xled.cli:main"]},
    include_package_data=True,
    install_requires=requirements,
    tests_require=tests_requirements,
    extras_require={
        "tests": tests_requirements,
    },  # noqa: E231
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2,!=3.3,!=3.4,!=3.5",
    license="MIT license",
    zip_safe=False,
    keywords="xled,twinkly",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    project_urls={
        "Documentation": "https://xled.readthedocs.io/",
        "Source": "https://github.com/scrool/xled",
        "Chanelog": "https://xled.readthedocs.io/en/latest/history.html",
    },
    test_suite="tests",
)
