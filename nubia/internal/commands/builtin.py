#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from nubia.internal import context
from nubia.internal.cmdbase import Command
from nubia.internal.interactive import IOLoop
from nubia.internal.io.eventbus import Message


class Connect(Command):
    """
    A pseudo command that implicitly gets called to start the interactive mode
    """

    cmds = {"connect": "Start the interactive mode"}

    def __init__(self):
        super(Connect, self).__init__()
        self._built_in = True

    def run_interactive(self, cmd, args, raw):
        return self._run()

    def run_cli(self, args):
        return self._run()

    def _run(self):
        self._command_registry.dispatch_message(Message.CONNECTED)
        return 0

    def get_command_names(self):
        return self.cmds.keys()

    def add_arguments(self, parser):
        parser.add_parser("connect")

    def get_help(self, cmd, *args):
        return self.cmds[cmd]


class Exit(Command):
    HELP = "Exits the program"
    cmd = ["quit", "q", "exit"]

    def __init__(self):
        super(Exit, self).__init__()
        self._built_in = True

    def run_interactive(self, cmd, args, raw):
        raise EOFError()
        return 0

    def get_command_names(self):
        return self.cmd

    def get_help(self, cmd, *args):
        return self.HELP


class Verbose(Command):
    """
    Changes verbosity level in interactive mode
    """

    HELP = "Prints or changes verbosity level, accepts integer or True/False"
    CMD = ":verbose"

    def __init__(self):
        super(Verbose, self).__init__()
        self._built_in = True

    def run_interactive(self, cmd, args, raw):
        ctx = context.get_context()
        if args:
            ctx.set_verbose(args)
        else:
            print("Current verbosity: {}".format(ctx.args.verbose))

    def get_command_names(self):
        return [self.CMD]

    def get_help(self, cmd, *args):
        return self.HELP
