#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

from nubia import command
from tests.util import TestShell


class SuperCommandSpecTest(unittest.TestCase):
    def test_super_basics(self):
        this = self

        @command
        class SuperCommand:
            "SuperHelp"

            @command
            def sub_command(self, arg1: str, arg2: int):
                "SubHelp"
                this.assertEqual(arg1, "giza")
                this.assertEqual(arg2, 22)
                return 45

            @command
            def another_command(self, arg1: str):
                "AnotherHelp"
                return 22

        shell = TestShell(commands=[SuperCommand])
        self.assertEqual(
            45,
            shell.run_cli_line(
                "test_shell super-command sub-command " "--arg1=giza --arg2=22"
            ),
        )
        self.assertEqual(
            22,
            shell.run_cli_line(
                "test_shell super-command another-command " "--arg1=giza"
            ),
        )

    def test_super_common_arguments(self):
        this = self

        @command
        class SuperCommand:
            "SuperHelp"

            def __init__(self, shared: int = 10) -> None:
                self.shared = shared

            @command
            def sub_command(self, arg1: str, arg2: int):
                "SubHelp"
                this.assertEqual(self.shared, 15)
                this.assertEqual(arg1, "giza")
                this.assertEqual(arg2, 22)
                return 45

        shell = TestShell(commands=[SuperCommand])
        self.assertEqual(
            45,
            shell.run_cli_line(
                "test_shell super-command --shared=15 "
                "sub-command --arg1=giza --arg2=22"
            ),
        )
        self.assertEqual(
            45,
            shell.run_cli_line(
                "test_shell super-command sub-command "
                "--arg1=giza --arg2=22 --shared=15"
            ),
        )
