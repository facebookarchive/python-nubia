#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from nubia.internal import context
from nubia.internal.cmdbase import Command
from nubia.internal.exceptions import UnknownCommand, CommandError
from prettytable import PrettyTable
from termcolor import cprint, colored


class HelpCommand(Command):
    HELP = "Prints help about all the commands"
    cmds = {"help": HELP, "?": HELP}

    def __init__(self):
        super(Command, self).__init__()
        self._built_in = True

    @property
    def registry(self):
        return context.get_context().registry

    def get_completions(self, cmd, document, complete_event):
        return self.registry.get_completer().get_completions(
            document, complete_event
        )

    def run_interactive(self, _0, args, _2):
        if args:
            args = args.split()
            try:
                cmd_instance = self.registry.find_command(args[0])
                if not cmd_instance:
                    raise UnknownCommand(
                        "Command `{}` is " "unknown".format(args[0])
                    )
                else:
                    help_msg = cmd_instance.get_help(args[0].lower(), *args)
                print(help_msg)
            except CommandError as e:
                cprint(str(e), "red")
                return 1
        else:
            built_ins = PrettyTable(["Command", "Description"])
            built_ins.align = "l"
            t = PrettyTable(["Command", "Description"])
            t.align = "l"

            commands = {
                cmd_name: cmd
                for cmd in self.registry.get_all_commands()
                for cmd_name in cmd.get_command_names()
            }

            for cmd_name in sorted(commands):
                cmd = commands[cmd_name]
                table = built_ins if cmd.built_in else t
                cmd_help = cmd.get_help(cmd_name)
                table.add_row([colored(cmd_name, "magenta"), cmd_help])

            print(t)

            cprint("Built-in Commands", "yellow")
            print(built_ins)
            return 0

    def get_command_names(self):
        return self.cmds.keys()

    def get_help(self, cmd, *args):
        return self.HELP
