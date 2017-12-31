#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `xled` package."""

from __future__ import absolute_import

import unittest
from click.testing import CliRunner

from xled import cli


class TestCLI(unittest.TestCase):
    """Tests for `xled` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_basics(self):
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert "Usage: main" in result.output
        help_result = runner.invoke(cli.main, ["--help"])
        assert help_result.exit_code == 0
        assert "Show this message and exit." in help_result.output
