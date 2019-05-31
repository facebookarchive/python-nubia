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
        self.assertEqual("my-function", cmd.name)
        self.assertEqual("HelpMessage", cmd.help)
        self.assertEqual(2, len(args))
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
        self.assertEqual("super-command", cmd.name)
        self.assertEqual("SuperHelp", cmd.help)
        self.assertEqual(0, len(args.keys()))
        self.assertEqual(1, len(data.subcommands))
        subcmd_attr, subcmd_insp = data.subcommands[0]
        self.assertEqual("my_function", subcmd_attr)
        subcmd = subcmd_insp.command
        self.assertEqual("my-function", subcmd.name)
        self.assertEqual("HelpMessage", subcmd.help)
        subargs = subcmd_insp.arguments
        self.assertEqual(2, len(subargs))
        self.assertTrue("arg1" in subargs.keys())
        self.assertTrue("argument-2" in subargs.keys())
