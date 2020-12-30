#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import sys

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "click-log",
    "Click>=6.0",
    "cryptography",
    "netaddr",
    "pyzmq>=17",
    "requests",
    "tornado>=5.0.0",
    "requests-toolbelt",
]
tests_requirements = ["vcrpy-unittest"]

if sys.version_info < (3, 3):
    requirements.append("ipaddress")
    requirements.append("monotonic")

setup(
    name="xled",
    # bumpversion v0.5.3 doesn't handle version string in double quotes
    # correctly so prevent Black to format it:
    # fmt: off
    version='0.6.1',
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
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
)
