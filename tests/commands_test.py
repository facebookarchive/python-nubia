#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from typing import List, Optional

from later.unittest import TestCase
from termcolor import cprint

from nubia import argument, command, deprecated
from tests.util import TestShell


class CommandSpecTest(TestCase):
    async def test_command_sync(self):
        @command
        def test_command() -> int:
            """
            Sample Docstring
            """
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, await shell.run_cli_line("test_shell test-command "))

    async def test_command_name_spec1(self):
        @command
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command(arg: List[str]) -> int:
            """
            Sample Docstring
            """
            self.assertEqual(["a", "b"], arg)
            cprint(arg, "green")
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            22, await shell.run_cli_line("test_shell test-command --arg a b")
        )

        self.assertEqual(
            22, await shell.run_interactive_line('test-command arg=["a","b"]')
        )
        self.assertEqual(
            22, await shell.run_interactive_line("test-command arg=[a, b]")
        )

    async def test_command_name_spec2(self):
        """
        Explicitly setting the command name with underscore, we should respect
        the supplied name and not auto-transform it
        """

        @command("bleh_command")
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command(arg: List[str]) -> int:
            """
            Sample Docstring
            """
            self.assertEqual(["a", "b"], arg)
            cprint(arg, "green")
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            22, await shell.run_cli_line("test_shell bleh_command --arg a b")
        )
        self.assertEqual(
            22, await shell.run_interactive_line('bleh_command arg=["a","b"]')
        )
        self.assertEqual(
            22, await shell.run_interactive_line("bleh_command arg=[a, b]")
        )

    async def test_command_async(self):
        @command
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command(arg: List[str]) -> int:
            """
            Sample Docstring
            """
            self.assertEqual(["a", "b"], arg)
            cprint(arg, "green")
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            22, await shell.run_cli_line("test_shell test-command --arg a b")
        )
        self.assertEqual(
            22, await shell.run_interactive_line('test-command arg=["a","b"]')
        )

    async def test_command_aliases_spec(self):
        """
        Testing aliases
        """

        @command("bleh_command", aliases=["bleh"])
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command(arg: List[str]) -> int:
            """
            Sample Docstring
            """
            self.assertEqual(["a", "b"], arg)
            cprint(arg, "green")
            return 22

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, await shell.run_cli_line("test_shell bleh -i a b"))

    async def test_command_find_approx_spec(self):
        """
        Testing approximate command / subcommand typing
        """

        @command("command_first", aliases=["first"])
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command_1(arg: int = 22) -> int:
            """
            Sample Docstring
            """
            cprint(arg, "green")
            return arg

        @command("command_second", aliases=["second"])
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command_2(arg: int = 23) -> int:
            """
            Sample Docstring
            """
            cprint(arg, "green")
            return arg

        shell = TestShell(commands=[test_command_1, test_command_2])

        # correct command name
        self.assertEqual(22, await shell.run_interactive_line("first"))
        # unique prefix command name
        self.assertEqual(22, await shell.run_interactive_line("f"))
        # unique levenshtein command name
        self.assertEqual(22, await shell.run_interactive_line("firts"))
        # unique prefix + levenshtein command name
        self.assertEqual(22, await shell.run_interactive_line("firs"))
        # non-unique prefix command name
        self.assertEqual(None, await shell.run_interactive_line("command"))

        # approximate matching only works for interactive mode, not CLI
        self.assertEqual(22, await shell.run_cli_line("test_shell first"))
        with self.assertRaises(SystemExit):
            await shell.run_cli_line("test_shell f")
        with self.assertRaises(SystemExit):
            await shell.run_cli_line("test_shell firts")
        with self.assertRaises(SystemExit):
            await shell.run_cli_line("test_shell firs")
        with self.assertRaises(SystemExit):
            await shell.run_cli_line("test_shell command")

    async def test_no_type_works_the_same(self):
        @command
        @argument("arg", positional=True)
        async def test_command(arg: str) -> int:
            """
            Sample Docstring
            """
            self.assertIsInstance(arg, str)
            self.assertEqual("1", arg)
            return 64 + int(arg)

        shell = TestShell(commands=[test_command])
        self.assertEqual(65, await shell.run_cli_line("test_shell test-command 1"))
        self.assertEqual(65, await shell.run_interactive_line("test-command 1"))
        self.assertEqual(65, await shell.run_interactive_line('test-command "1"'))

        @command
        @argument("arg")
        async def test_command(arg: str) -> int:
            """
            Sample Docstring
            """
            self.assertIsInstance(arg, str)
            self.assertEqual("1", arg)
            return 64 + int(arg)

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            65, await shell.run_cli_line("test_shell test-command --arg 1")
        )
        self.assertEqual(
            65,
            await shell.run_interactive_line("test-command arg=1"),
        )
        self.assertEqual(
            65,
            await shell.run_interactive_line('test-command arg="1"'),
        )

    async def test_command_with_postional(self):
        @command
        @argument("arg1", positional=True)
        @argument("arg2", positional=True)
        @argument("arg3", positional=True)
        async def test_command(arg1: str, arg2: str, arg3: str) -> int:
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
            66, await shell.run_cli_line("test_shell test-command 1 2 nubia")
        )
        self.assertEqual(66, await shell.run_interactive_line("test-command 1 2 nubia"))

    async def test_command_with_extra_spaces(self):
        @command
        @argument("arg1", positional=True)
        async def test_command(arg1: str) -> None:
            """
            Sample Docstring
            """
            self.assertEqual("1", arg1)
            self.assertIsInstance(arg1, str)
            return True

        shell = TestShell(commands=[test_command])
        self.assertTrue(await shell.run_interactive_line("test-command 1"))
        self.assertTrue(await shell.run_interactive_line("test-command  1"))
        self.assertTrue(await shell.run_interactive_line("test-command   1"))
        self.assertTrue(await shell.run_interactive_line(" test-command 1"))
        self.assertTrue(await shell.run_interactive_line("  test-command 1"))
        self.assertTrue(await shell.run_interactive_line("test-command 1 "))
        self.assertTrue(await shell.run_interactive_line("test-command 1  "))
        self.assertTrue(await shell.run_interactive_line("  test-command  1  "))

    async def test_command_with_postional_and_named_arguments(self):
        @command
        @argument("arg2", positional=True)
        @argument("arg3", positional=True)
        async def test_command(arg1: str, arg2: str, arg3: str) -> int:
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
            66, await shell.run_cli_line("test_shell test-command --arg1=1 2 nubia")
        )
        self.assertEqual(
            66, await shell.run_interactive_line("test-command arg1=1 2 nubia")
        )
        self.assertEqual(
            66, await shell.run_interactive_line("test-command arg1=1 arg2=2 nubia")
        )
        # Fails parsing because positionals have to be at the end
        self.assertEqual(
            1, await shell.run_interactive_line("test-command 2 nubia arg1=1")
        )

    async def test_command_with_mutex_groups(self):
        @command(exclusive_arguments=["arg1", "arg2"])
        @argument("arg1")
        @argument("arg2")
        async def test_command(arg1: str = "0", arg2: str = "0") -> int:
            """
            Sample Docstring
            """
            return 64 * int(arg1) + int(arg2)

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            64, await shell.run_cli_line("test_shell test-command --arg1 1")
        )
        self.assertEqual(
            64,
            await shell.run_interactive_line("test-command arg1=1"),
        )

        self.assertEqual(
            2, await shell.run_cli_line("test_shell test-command --arg2 2")
        )
        self.assertEqual(
            2,
            await shell.run_interactive_line("test-command arg2=2"),
        )

        with self.assertRaises(SystemExit):
            await shell.run_cli_line("test_shell test-command --arg1 1 --arg2 2")

        self.assertEqual(
            66,
            await shell.run_interactive_line("test-command arg1=1 arg2=2"),
            "We are not enforsing mutex groups on interactive",
        )

    async def test_command_with_mutex_groups_two_positionals(self):
        msg = "We don't supporting mutex group with required arguments"
        with self.assertRaises(ValueError, msg=msg):

            @command(exclusive_arguments=["arg1", "arg2"])
            @argument("arg1", positional=True)
            @argument("arg2")
            async def test_command(arg1: str, arg2: str = "lalala") -> int:
                """
                Sample Docstring
                """
                return -1

            await TestShell(commands=[test_command]).run_async()

    async def test_command_default_argument(self):
        """
        Tests that calling a command from the CLI without all arguments
        specified will fall back to the default arguments set in the command
        definition.
        """

        @command
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command(arg: int = 22) -> int:
            """
            Sample Docstring
            """
            cprint(arg, "green")
            return arg

        shell = TestShell(commands=[test_command])
        self.assertEqual(22, await shell.run_cli_line("test_shell test-command"))
        self.assertEqual(22, await shell.run_interactive_line("test-command"))

    async def test_command_optional_argument(self):
        """
        Same as above but check for make the argument optional in Python sense.
        """

        @command
        @argument("arg", description="argument help", aliases=["i"])
        async def test_command(arg: Optional[List[str]] = None) -> int:
            """
            Sample Docstring
            """
            arg = arg or ["42"]
            cprint(arg, "green")
            return sum(int(x) for x in arg)

        shell = TestShell(commands=[test_command])
        self.assertEqual(42, await shell.run_cli_line("test_shell test-command"))
        self.assertEqual(42, await shell.run_interactive_line("test-command"))
        self.assertEqual(0, await shell.run_cli_line("test_shell test-command --arg 0"))
        self.assertEqual(
            0,
            await shell.run_interactive_line("test-command arg=[0]"),
        )

    async def test_command_one_required_one_default_argument(self):
        """
        Tests that calling a command from the CLI without all arguments
        specified will fall back to the default arguments set in the command
        definition.
        """

        @command("bleh_command")
        @argument("arg1", description="argument help", aliases=["i1"])
        @argument("arg2", description="argument 2 help", aliases=["i2"])
        async def test_command(arg1: int, arg2: int = 1) -> int:
            """
            Sample Docstring
            """
            cprint(arg1, "green")
            return arg1 + arg2

        shell = TestShell(commands=[test_command])
        self.assertEqual(
            22, await shell.run_cli_line("test_shell bleh_command --arg1=21")
        )
        self.assertEqual(
            22,
            await shell.run_interactive_line("bleh_command arg1=21"),
        )

    async def test_command_for_blacklist_plugin_allowed(self):
        @command("allowed")
        async def test_command():
            """
            Sample Docstring
            """
            cprint("Command Executed as required", "green")
            return 42

        shell = TestShell(commands=[test_command])
        self.assertEqual(42, await shell.run_cli_line("test_shell allowed"))
        self.assertEqual(42, await shell.run_interactive_line("allowed"))

    async def test_command_for_blacklist_plugin_blacklisted(self):
        @command("blocked")
        async def test_command():
            """
            Sample Docstring
            """
            cprint("Command executed, but should be blocked", "red")
            return 3

        shell = TestShell(commands=[test_command])
        self.assertEqual(1, await shell.run_cli_line("test_shell blocked"))
        self.assertEqual(1, await shell.run_interactive_line("blocked"))

    async def test_command_with_negative_ints(self):
        @command("minus_command")
        @argument("arg1", type=int)
        async def test_command(arg1):
            """
            Sample Docstring
            """
            self.assertEqual(type(5), type(arg1))
            return 42 if arg1 == -1 else -1

        shell = TestShell(commands=[test_command])
        # Cli run
        self.assertEqual(
            42, await shell.run_cli_line("test_shell minus_command --arg1=-1")
        )
        # Interactive
        self.assertEqual(42, await shell.run_interactive_line("minus_command arg1=-1"))

    async def test_command_with_negative_floats(self):
        @command("minus_command")
        @argument("arg1", type=float)
        async def test_command(arg1):
            """
            Sample Docstring
            """
            self.assertEqual(type(5.0), type(arg1))
            return 42 if arg1 == -1.0 else 55

        shell = TestShell(commands=[test_command])
        # Cli run
        self.assertEqual(
            42, await shell.run_cli_line("test_shell minus_command --arg1=-1")
        )
        self.assertEqual(
            42, await shell.run_cli_line("test_shell minus_command --arg1=-1.0")
        )
        # Interactive
        self.assertEqual(42, await shell.run_interactive_line("minus_command arg1=-1"))
        self.assertEqual(
            42, await shell.run_interactive_line("minus_command arg1=-1.0")
        )

    async def test_command_deprecation(self):
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
        self.assertEqual(42, await shell.run_cli_line("test_shell old-command"))
        self.assertEqual(42, await shell.run_interactive_line("old-command"))
        self.assertEqual(42, await shell.run_cli_line("test_shell new-command"))
        self.assertEqual(42, await shell.run_interactive_line("new-command"))

    async def test_type_lifting(self):
        @command
        @argument("args")
        async def test_command(args: List[str]) -> str:
            """
            Sample Docstring
            """
            return "|".join(args)

        shell = TestShell(commands=[test_command])
        # CLI
        self.assertEqual(
            "a", await shell.run_cli_line("test_shell test-command --args a")
        )
        self.assertEqual(
            "a|b", await shell.run_cli_line("test_shell test-command --args a b")
        )
        # Interactive
        self.assertEqual("a", await shell.run_interactive_line('test-command args="a"'))
        self.assertEqual(
            "a", await shell.run_interactive_line('test-command args=["a"]')
        )
        self.assertEqual(
            "a|b", await shell.run_interactive_line('test-command args=["a", "b"]')
        )
