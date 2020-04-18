#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#
import os
import sys
import tempfile
import unittest
from nubia import argument, command
from tests.util import TestShell

class ReadStdinTest(unittest.TestCase):
    def test_read_from_stdin(self):
        @command
        @argument("arg")
        def test_command(arg: str) -> int:
            """
            Sample Docstring
            """
            self.assertEqual("test_arg", arg)
            return 22

        command_file = tempfile.NamedTemporaryFile(
            mode="w+",
            prefix="test_read_from_stdin",
            delete=True
        )
        command_file.write("test-command arg=test_arg")
        command_file.flush()
        os.lseek(command_file.fileno(), 0, os.SEEK_SET)
        os.dup2(command_file.fileno(), sys.stdin.fileno())
        shell = TestShell(commands=[test_command])
        self.assertEqual(22, shell.run(cli_args=["", "connect"]))
