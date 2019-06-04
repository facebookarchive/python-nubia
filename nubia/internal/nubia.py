#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse
import codecs
import locale
import logging
import os
import sys
import tempfile
import traceback
import typing
from termcolor import cprint

from nubia.internal import context
from nubia.internal import exceptions
from nubia.internal.options import Options
from nubia.internal.typing.argparse import create_subparser_class
from nubia.internal.blackcmd import CommandBlacklist
from nubia.internal.cmdbase import AutoCommand
from nubia.internal import cmdloader
from nubia.internal.commands import builtin
from nubia.internal.commands import help
from nubia.internal.helpers import catchall
from nubia.internal.interactive import IOLoop
from nubia.internal.io import logger
from nubia.internal.plugin_interface import PluginInterface
from nubia.internal.registry import CommandsRegistry
from nubia.internal.usage_logger_interface import UsageLoggerInterface


def set_default_subparser(self, name, args=None):
    """default subparser selection. Call after setup, just before parse_args()
    name: is the name of the subparser to call by default
    args: if set is the argument list handed to parse_args()

    tested with 2.7, 3.2, 3.3, 3.4
    it works with 2.6 assuming argparse is installed
    """
    subparser_found = False
    for arg in sys.argv[1:]:
        if arg in ["-h", "--help"]:  # global help if no subparser
            break
    else:
        for x in self._subparsers._actions:
            if not isinstance(x, argparse._SubParsersAction):
                continue
            for sp_name in x._name_parser_map.keys():
                if sp_name in sys.argv[1:]:
                    subparser_found = True
        if not subparser_found:
            # insert default in the last position, this implies no
            # global options without a sub_parsers specified
            if args is None:
                sys.argv.append(name)
            else:
                args.append(name)


# Injects this method in ArgumentParser, this is to support default subparsers
# in Python < 3 while it also works with python > 3
argparse.ArgumentParser.set_default_subparser = set_default_subparser


class Nubia(object):
    """
    This is the core class that creates and runs nubia, the constructor takes
    a number of arguments that control how nubia should behave and which
    plugin it will load on startup.
    """

    def __init__(
        self,
        name,
        command_pkgs=None,
        plugin: typing.Optional[PluginInterface] = None,
        testing: bool = False,
        options: typing.Optional[Options] = None,
    ):
        self._name = name
        self._plugin = plugin or PluginInterface()
        self._options = options or Options()
        assert isinstance(self._plugin, PluginInterface)
        self._blacklist = self._plugin.getBlacklistPlugin()
        self._command_pkgs = command_pkgs
        if self._blacklist is not None:
            assert isinstance(self._blacklist, CommandBlacklist)

        self._testing = testing

        # Setting the context to be global
        context._ctx = self._plugin.create_context()
        self._ctx = context.get_context()
        assert isinstance(self._ctx, context.Context)
        # Setting the binary name
        self._ctx.set_binary_name(self._name)

        # Load, setup the usagelogger
        self._usagelogger = None

        self._opts_parser = self._plugin.get_opts_parser()
        SubParser = create_subparser_class(self._opts_parser)
        self._opts_parser.add_argument(
            "--_print-completion-model", action="store_true", help=argparse.SUPPRESS
        )

        cmd_parser = self._opts_parser.add_subparsers(
            dest="_cmd",
            help="Subcommand to run, if missing the interactive mode is started"
            " instead.",
            parser_class=SubParser,
            metavar="[command]",
        )

        builtin_cmds = [
            builtin.Connect,
            builtin.Exit,
            builtin.Verbose,
            help.HelpCommand,
        ]

        listeners = self._plugin.get_listeners()
        self._registry = CommandsRegistry(cmd_parser, listeners)
        self._ctx.set_registry(self._registry)
        self._registry.register_priority_listener(self._ctx)
        # register built-in commands
        for cmd in builtin_cmds:
            self._registry.register_command(cmd())

        # load commands from plugin
        for cmd in self._plugin.get_commands():
            self._registry.register_command(cmd, override=True)
        # load commands from command packages
        if not isinstance(self._command_pkgs, list):
            self._command_pkgs = [self._command_pkgs]
        for pkg in self._command_pkgs:
            for cmd in cmdloader.load_commands(pkg):
                self._registry.register_command(AutoCommand(cmd), override=True)

        # By default, if we didn't receive any command we will use the connect
        # command which drops us to an interactive mode.
        self._opts_parser.set_default_subparser("connect")

    def _setup_logging(self, args):
        root_logger = self._plugin.setup_logging(logging.root, args)
        if root_logger:
            return

        if args.verbose and args.verbose >= 2:
            logging_level = logging.DEBUG
        elif args.verbose == 1:
            logging_level = logging.INFO
        else:
            logging_level = logging.WARN

        if args.stderr:
            logging_stream = sys.stderr
        else:
            logging_stream = tempfile.NamedTemporaryFile(
                mode="w+",  # default is 'w+b', oddly enough
                prefix="{}-".format(self._name),
                delete=False,
            )
            print("Logging to {}".format(logging_stream.name), file=sys.stderr)

        logger.setup_logger(level=logging_level, stream=logging_stream)

    def start_ipython(self, args):
        from nubia.internal.ipython import start_interactive_python

        return start_interactive_python(self._plugin, self._registry, self._ctx, args)

    @property
    def usage_logger(self):
        if not self._usagelogger:
            self._usagelogger = self._plugin.create_usage_logger(
                self._ctx
            ) or UsageLoggerInterface(self._ctx)
            assert isinstance(self._usagelogger, UsageLoggerInterface)
        return self._usagelogger

    def _setup_terminal(self, args):
        # Setup the codec for writing unicode to stdout. This also correctly
        # encodes unicode if the standard output is ascii and prevents python
        # from crashing with UnicodeEncodingError
        # Only required for Python 2
        if sys.version_info[0] == 2:
            writer = codecs.getwriter(locale.getpreferredencoding())
            sys.stdout = writer(sys.stdout)

        if getattr(args, "no_color", False) or not sys.stdout.isatty():
            os.environ["ANSI_COLORS_DISABLED"] = "True"

    def _create_interactive_io_loop(self, args):
        io_loop = IOLoop(self._ctx, self._plugin, self.usage_logger, self._options)
        self._ctx.on_interactive(args)
        return io_loop

    def start_interactive(self, args):
        io_loop = self._create_interactive_io_loop(args)
        ret = 0
        # Only run the Interactive mode if std is a tty, otherwise
        # we should rad the input from stdin, process it, and exit.
        if sys.stdin.isatty():
            io_loop.run()
            return ret
        else:
            # Read the command from stdin and run
            commands = sys.stdin.readlines()
            for command in commands:
                # execute
                print("> {}".format(command))
                ret = io_loop.parse_and_evaluate(sys.stdout, command)
                # We fail execution on the first failing command
                if ret:
                    return ret
            return ret

    def _parse_args(self, cli_args=sys.argv):
        cli_args = cli_args[1:]  # remove binary name
        args, extra = self._opts_parser.parse_known_args(args=cli_args)
        # this allows subcommand specific args to be inserted anywhere in the
        # cli, for instance:
        #   my_prog --atonce=5 -vv -t <tier> status --stderr
        # It essentially puts all unrecognized args in the end of the cli
        # invocation and try parsing again
        if extra:
            for extra_arg in extra:
                cli_args.remove(extra_arg)
                cli_args.append(extra_arg)
            args = self._opts_parser.parse_args(args=cli_args)
        return args

    def _validate_args(self, args):
        try:
            # The argument validation will raise ArgsValidationError
            self._plugin.validate_args(args)
        except exceptions.ArgsValidationError as e:
            cprint("Arguments validation error: {}".format(str(e)), "red")
            return 1
        except Exception as e:
            cprint(
                "An exception occurred while validating the command "
                "arguments: {}".format(str(e)),
                "red",
            )
            return 1

    def run_cli(self, args):
        catchall(self.usage_logger.pre_exec)
        try:
            ret = self._blacklist.is_blacklisted(args._cmd)
            if ret:
                return ret
        except Exception as e:
            err_message = (
                "Blacklist executing failed, "
                "all commands are available.\n"
                "{}".format(str(e))
            )
            cprint(err_message, "red")
            logging.error(err_message)
        self._ctx.on_cli(args._cmd, args)
        ret = self._registry.find_command(args._cmd).run_cli(args)
        return ret

    def _pre_run(self, cli_args):
        args = self._parse_args(cli_args)
        self._setup_logging(args)
        # check if we can add colors to sdout
        self._setup_terminal(args)

        self._validate_args(args)

        self._ctx.set_args(args)
        self._registry.set_cli_args(args)
        return args

    def run(self, cli_args=sys.argv, ipython=False):
        """
        Runs nubia either in interactive or cli (or parsing commands from
        stdin) based on the cli_args supplied (defaults to sys.argv). This will
        block until the shell is done processing all the input and will return
        the exit code.
        """
        args = self._pre_run(cli_args)

        if args._print_completion_model:
            from nubia.internal import registry_tools as regtools

            try:
                data = regtools.export_registry(
                    self._plugin, args, self._opts_parser, self._registry
                )
                print(data)
                return 0
            except Exception as e:
                print("Failed to export model: {}".format(e), file=sys.stderr)
                traceback.print_exc()
                return 1
        if ipython:
            return self.start_ipython(args)
        # by default, if no command is passed we will get 'connect'
        if args._cmd == "connect":
            return self.start_interactive(args)
        else:
            ret = self.run_cli(args)
            catchall(self.usage_logger.post_exec, args._cmd, cli_args, ret, True)

        if type(ret) is int:
            return ret

        if type(ret) is bool:
            return int(not (ret))

        if ret is None:
            return 0
        else:
            return 1
