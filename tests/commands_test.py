#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import unittest
from typing import List, Optional

from termcolor import cprint

from nubia import argument, command, deprecated
from tests.util import TestShell


class CommandSpecTest(unittest.TestCase):
    def test_command_name_spec1(self):
        @command
        @argument("arg", description="argument help", aliases=["i"])
        def test_command(arg: List[str]) -> int:
            """
            Sample Docstring
            """
            self.assertEqual(["a", "b"], arg)
            cprint(arg, "green")
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, shell.run_cli_line("test_shell test-command --arg a b"))
        self.assertEqual(22, shell.run_interactive_line('test-command arg=["a","b"]'))
        self.assertEqual(22, shell.run_interactive_line("test-command arg=[a, b]"))

    def test_command_name_spec2(self):
        """
        Explicitly setting the command name with underscore, we should respect
        the supplied name and not auto-transform it
        """

        @command("bleh_command")
        @argument("arg", description="argument help", aliases=["i"])
        def test_command(arg: List[str]) -> int:
            """
            Sample Docstring
            """
            self.assertEqual(["a", "b"], arg)
            cprint(arg, "green")
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, shell.run_cli_line("test_shell bleh_command --arg a b"))
        self.assertEqual(22, shell.run_interactive_line('bleh_command arg=["a","b"]'))
        self.assertEqual(22, shell.run_interactive_line("bleh_command arg=[a, b]"))

    def test_no_type_works_the_same(self):
        @command
        @argument("arg", positional=True)
        def test_command(arg: str) -> int:
            """
            Sample Docstring
            """
            self.assertIsInstance(arg, str)
            self.assertEqual("1", arg)
            return 64 + int(arg)

        shell = TestShell(commands=[test_command])
        self.assertEqual(65, shell.run_cli_line("test_shell test-command 1"))
        self.assertEqual(65, shell.run_interactive_line("test-command 1"))
        self.assertEqual(65, shell.run_interactive_line('test-command "1"'))

        @command
        @argument("arg")
        def test_command(arg: str) -> int:
            """
            Sample Docstring
            """
            self.assertIsInstance(arg, str)
            self.assertEqual("1", arg)
            return 64 + int(arg)

        shell = TestShell(commands=[test_command])
        self.assertEqual(65, shell.run_cli_line("test_shell test-command --arg 1"))
        self.assertEqual(65, shell.run_interactive_line("test-command arg=1"))
        self.assertEqual(65, shell.run_interactive_line('test-command arg="1"'))

    def test_command_with_postional(self):
        @command
        @argument("arg1", positional=True)
        @argument("arg2", positional=True)
        @argument("arg3", positional=True)
        def test_command(arg1: str, arg2: str, arg3: str) -> int:
            """
            Sample Docstring
            """
            cprint([arg1, arg2])
            self.assertEqual("1", arg1)
            self.assertIsInstance(arg1, str)
            self.assertEqual("2", arg2)
            self.assertIsInstance(arg2, str)
            self.assertEqual("nubia", arg3)
            return 64 * int(arg1) + int(arg2)

        shell = TestShell(commands=[test_command])
        self.assertEqual(66, shell.run_cli_line("test_shell test-command 1 2 nubia"))
        self.assertEqual(66, shell.run_interactive_line("test-command 1 2 nubia"))

    def test_command_with_postional_and_named_arguments(self):
        @command
        @argument("arg2", positional=True)
        @argument("arg3", positional=True)
        def test_command(arg1: str, arg2: str, arg3: str) -> int:
            """
            Sample Docstring
            """
            cprint([arg1, arg2])
            self.assertEqual("1", arg1)
            self.assertIsInstance(arg1, str)
            self.assertEqual("2", arg2)
            self.assertIsInstance(arg2, str)
            self.assertEqual("nubia", arg3)
            return 64 * int(arg1) + int(arg2)

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            66, shell.run_cli_line("test_shell test-command --arg1=1 2 nubia")
        )
        self.assertEqual(66, shell.run_interactive_line("test-command arg1=1 2 nubia"))
        self.assertEqual(
            66, shell.run_interactive_line("test-command arg1=1 arg2=2 nubia")
        )
        # Fails parsing because positionals have to be at the end
        self.assertEqual(1, shell.run_interactive_line("test-command 2 nubia arg1=1"))

    def test_command_with_mutex_groups(self):
        @command(exclusive_arguments=["arg1", "arg2"])
        @argument("arg1")
        @argument("arg2")
        def test_command(arg1: str = "0", arg2: str = "0") -> int:
            """
            Sample Docstring
            """
            return 64 * int(arg1) + int(arg2)

        shell = TestShell(commands=[test_command])
        self.assertEqual(64, shell.run_cli_line("test_shell test-command --arg1 1"))
        self.assertEqual(64, shell.run_interactive_line("test-command arg1=1"))

        self.assertEqual(2, shell.run_cli_line("test_shell test-command --arg2 2"))
        self.assertEqual(2, shell.run_interactive_line("test-command arg2=2"))

        with self.assertRaises(SystemExit):
            shell.run_cli_line("test_shell test-command --arg1 1 --arg2 2")

        self.assertEqual(
            66,
            shell.run_interactive_line("test-command arg1=1 arg2=2"),
            "We are not enforsing mutex groups on interactive",
        )

    def test_command_with_mutex_groups_two_positionals(self):
        msg = "We don't supporting mutex group with required arguments"
        with self.assertRaises(ValueError, msg=msg):

            @command(exclusive_arguments=["arg1", "arg2"])
            @argument("arg1", positional=True)
            @argument("arg2")
            def test_command(arg1: str, arg2: str = "lalala") -> int:
                """
                Sample Docstring
                """
                return -1

            TestShell(commands=[test_command])

    def test_command_default_argument(self):
        """
        Tests that calling a command from the CLI without all arguments
        specified will fall back to the default arguments set in the command
        definition.
        """

        @command
        @argument("arg", description="argument help", aliases=["i"])
        def test_command(arg: int = 22) -> int:
            """
            Sample Docstring
            """
            cprint(arg, "green")
            return arg

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, shell.run_cli_line("test_shell test-command"))
        self.assertEqual(22, shell.run_interactive_line("test-command"))

    def test_command_optional_argument(self):
        """
        Same as above but check for make the argument optional in Python sense.
        """

        @command
        @argument("arg", description="argument help", aliases=["i"])
        def test_command(arg: Optional[List[str]] = None) -> int:
            """
            Sample Docstring
            """
            arg = arg or ["42"]
            cprint(arg, "green")
            return sum(int(x) for x in arg)

        shell = TestShell(commands=[test_command])
        self.assertEqual(42, shell.run_cli_line("test_shell test-command"))
        self.assertEqual(42, shell.run_interactive_line("test-command"))
        self.assertEqual(0, shell.run_cli_line("test_shell test-command --arg 0"))
        self.assertEqual(0, shell.run_interactive_line("test-command arg=[0]"))

    def test_command_one_required_one_default_argument(self):
        """
        Tests that calling a command from the CLI without all arguments
        specified will fall back to the default arguments set in the command
        definition.
        """

        @command("bleh_command")
        @argument("arg1", description="argument help", aliases=["i1"])
        @argument("arg2", description="argument 2 help", aliases=["i2"])
        def test_command(arg1: int, arg2: int = 1) -> int:
            """
            Sample Docstring
            """
            cprint(arg1, "green")
            return arg1 + arg2

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, shell.run_cli_line("test_shell bleh_command --arg1=21"))
        self.assertEqual(22, shell.run_interactive_line("bleh_command arg1=21"))

    def test_command_for_blacklist_plugin_allowed(self):
        @command("allowed")
        def test_command():
            """
            Sample Docstring
            """
            cprint("Command Executed as required", "green")
            return 42

        shell = TestShell(commands=[test_command])
        self.assertEqual(42, shell.run_cli_line("test_shell allowed"))
        self.assertEqual(42, shell.run_interactive_line("allowed"))

    def test_command_for_blacklist_plugin_blacklisted(self):
        @command("blocked")
        def test_command():
            """
            Sample Docstring
            """
            cprint("Command executed, but should be blocked", "red")
            return 3

        shell = TestShell(commands=[test_command])
        self.assertEqual(1, shell.run_cli_line("test_shell blocked"))
        self.assertEqual(1, shell.run_interactive_line("blocked"))

    def test_command_with_negative_ints(self):
        @command("minus_command")
        @argument("arg1", type=int)
        def test_command(arg1):
            """
            Sample Docstring
            """
            self.assertEquals(type(5), type(arg1))
            return 42 if arg1 == -1 else -1

        shell = TestShell(commands=[test_command])
        # Cli run
        self.assertEqual(42, shell.run_cli_line("test_shell minus_command --arg1=-1"))
        # Interactive
        self.assertEqual(42, shell.run_interactive_line("minus_command arg1=-1"))

    def test_command_with_negative_floats(self):
        @command("minus_command")
        @argument("arg1", type=float)
        def test_command(arg1):
            """
            Sample Docstring
            """
            self.assertEquals(type(5.0), type(arg1))
            return 42 if arg1 == -1.0 else 55

        shell = TestShell(commands=[test_command])
        # Cli run
        self.assertEqual(42, shell.run_cli_line("test_shell minus_command --arg1=-1"))
        self.assertEqual(42, shell.run_cli_line("test_shell minus_command --arg1=-1.0"))
        # Interactive
        self.assertEqual(42, shell.run_interactive_line("minus_command arg1=-1"))
        self.assertEqual(42, shell.run_interactive_line("minus_command arg1=-1.0"))

    def test_command_deprecation(self):
        @deprecated(superseded_by="new-command")
        @command
        def old_command() -> int:
            """
            Sample Docstring
            """
            cprint("This command is deprecated", "yellow")
            return new_command()

        @command
        def new_command() -> int:
            """
            Sample Docstring
            """
            cprint("This is the future", "green")
            return 42

        shell = TestShell(commands=[old_command, new_command])
        self.assertEqual(42, shell.run_cli_line("test_shell old-command"))
        self.assertEqual(42, shell.run_interactive_line("old-command"))
        self.assertEqual(42, shell.run_cli_line("test_shell new-command"))
        self.assertEqual(42, shell.run_interactive_line("new-command"))

    def test_type_lifting(self):
        @command
        @argument("args")
        def test_command(args: List[str]) -> str:
            """
            Sample Docstring
            """
            return "|".join(args)

        shell = TestShell(commands=[test_command])
        # CLI
        self.assertEqual("a", shell.run_cli_line("test_shell test-command --args a"))
        self.assertEqual(
            "a|b", shell.run_cli_line("test_shell test-command --args a b")
        )
        # Interactive
        self.assertEqual("a", shell.run_interactive_line('test-command args="a"'))
        self.assertEqual("a", shell.run_interactive_line('test-command args=["a"]'))
        self.assertEqual(
            "a|b", shell.run_interactive_line('test-command args=["a", "b"]')
        )
