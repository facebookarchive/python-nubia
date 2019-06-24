#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

from nubia import command
from nubia.internal.typing import inspect_object


class InspectionTest(unittest.TestCase):
    def test_inspect_function1(self):
        @command
        def my_function(arg1: str, argument_2: int):
            """HelpMessage"""
            pass

        data = inspect_object(my_function)
        cmd = data.command
        args = data.arguments
        self.assertEquals("my-function", cmd.name)
        self.assertEquals("HelpMessage", cmd.help)
        self.assertEquals(2, len(args))
        self.assertTrue("arg1" in args.keys())
        self.assertTrue("argument-2" in args.keys())

    def test_inspect_class(self):
        @command
        class SuperCommand:
            """SuperHelp"""

            @command
            def my_function(self, arg1: str, argument_2: int):
                """HelpMessage"""
                pass

        data = inspect_object(SuperCommand)
        cmd = data.command
        args = data.arguments
        self.assertEquals("super-command", cmd.name)
        self.assertEquals("SuperHelp", cmd.help)
        self.assertEquals(0, len(args.keys()))
        self.assertEquals(1, len(data.subcommands))
        subcmd_attr, subcmd_insp = data.subcommands[0]
        self.assertEquals("my_function", subcmd_attr)
        subcmd = subcmd_insp.command
        self.assertEquals("my-function", subcmd.name)
        self.assertEquals("HelpMessage", subcmd.help)
        subargs = subcmd_insp.arguments
        self.assertEquals(2, len(subargs))
        self.assertTrue("arg1" in subargs.keys())
        self.assertTrue("argument-2" in subargs.keys())

    def test_inspect_no_docstring(self):
        @command
        class SuperCommand:
            """SuperHelp"""

            @command
            def my_function(self, arg1: str):
                pass

        data = inspect_object(SuperCommand)
        self.assertListEqual([], data.subcommands)
