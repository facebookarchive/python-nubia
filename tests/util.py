#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import sys

from nubia import Nubia, PluginInterface
from nubia.internal.blackcmd import CommandBlacklist
from nubia.internal.cmdbase import AutoCommand, Command


class TestPlugin(PluginInterface):
    def __init__(self, commands):
        self._commands = commands

    def get_commands(self):
        return [c if isinstance(c, Command) else AutoCommand(c) for c in self._commands]

    def getBlacklistPlugin(self):
        commandBlacklist = CommandBlacklist()
        commandBlacklist.add_blocked_command("blocked")
        return commandBlacklist


class TestShell(Nubia):
    def __init__(self, commands, name="test_shell"):
        super(TestShell, self).__init__(name, plugin=TestPlugin(commands), testing=True)

    async def run_cli_line(self, raw_line):
        cli_args_list = raw_line.split()
        args = await self._pre_run(cli_args_list)
        return await self.run_cli(args)

    async def run_interactive_line(self, raw_line, cli_args=None):
        cli_args = cli_args or "test_shell connect"
        cli_args_list = cli_args.split()
        args = await self._pre_run(cli_args_list)
        io_loop = self._create_interactive_io_loop(args)
        return await io_loop.parse_and_evaluate(raw_line)
