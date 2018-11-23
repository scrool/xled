#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["cryptography", "netaddr", "requests"]
tests_requirements = ["vcrpy-unittest"]

setup(
    name="xled",
    # bumpversion v0.5.3 doesn't handle version string in double quotes
    # correctly so prevent Black to format it:
    # fmt: off
    version='0.2.1',
    # fmt: on
    description=(
        "Python library for Twinkly - Smart Decoration LED lights for Christmas."
    ),
    long_description=readme + "\n\n" + history,
    author="Pavol Babinčák",
    author_email="scroolik@gmail.com",
    url="https://github.com/scrool/xled",
    packages=find_packages(include=["xled"]),
    include_package_data=True,
    install_requires=requirements,
    tests_require=tests_requirements,
    license="MIT license",
    zip_safe=False,
    keywords="xled,twinkly",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    test_suite="tests",
)
