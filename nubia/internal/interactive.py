#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import logging

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit import CommandLineInterface, Application, AbortAction
from prompt_toolkit.shortcuts import create_prompt_layout, create_eventloop
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Always, HasFocus, IsDone
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.layout.processors import (
    ConditionalProcessor,
    HighlightMatchingBracketProcessor,
)
from prompt_toolkit.buffer import Buffer
from termcolor import cprint
from nubia.internal.ui.lexer import NubiaLexer
from pygments.token import Token

import getpass
import os

from nubia.internal.io.eventbus import Listener
from nubia.internal.helpers import catchall
from nubia.internal.ui.style import shell_style


def split_command(text):
    return text.split(" ", 1)


class IOLoop(Listener):
    _tier = ""
    stop_requested = False

    def __init__(self, context, plugin, usagelogger):
        self._ctx = context
        self._command_registry = self._ctx.registry
        self._plugin = plugin
        self._blacklist = self._plugin.getBlacklistPlugin()

        self._status_bar = self._plugin.get_status_bar(context)
        self._manager = KeyBindingManager(
            enable_abort_and_exit_bindings=True,
            enable_system_bindings=True,
            enable_search=True,
            enable_auto_suggest_bindings=True,
        )
        self._registry = self._manager.registry
        self._cli = None
        self._suggestor = AutoSuggestFromHistory()
        self._completer = ShellCompleter(self._command_registry)
        self._command_registry.register_listener(self)
        self._usagelogger = usagelogger

    def _build_cli(self):
        eventloop = create_eventloop()

        history = FileHistory(
            os.path.join(
                os.path.expanduser("~"),
                ".{}_history".format(self._ctx.binary_name),
            )
        )

        layout = create_prompt_layout(
            lexer=PygmentsLexer(NubiaLexer),
            reserve_space_for_menu=5,
            get_prompt_tokens=self.get_prompt_tokens,
            get_rprompt_tokens=self._status_bar.get_rprompt_tokens,
            get_bottom_toolbar_tokens=self._status_bar.get_tokens,
            display_completions_in_columns=False,
            multiline=True,
            extra_input_processors=[
                ConditionalProcessor(
                    processor=HighlightMatchingBracketProcessor(chars="[](){}"),
                    filter=HasFocus(DEFAULT_BUFFER) & ~IsDone(),
                )
            ],
        )

        buf = Buffer(
            completer=self._completer,
            history=history,
            auto_suggest=self._suggestor,
            complete_while_typing=Always(),
            accept_action=AcceptAction.RETURN_DOCUMENT,
        )

        application = Application(
            style=shell_style,
            buffer=buf,
            key_bindings_registry=self._registry,
            layout=layout,
            on_exit=AbortAction.RAISE_EXCEPTION,
            on_abort=AbortAction.RETRY,
            ignore_case=True,
        )

        cli = CommandLineInterface(application=application, eventloop=eventloop)
        return cli

    def get_prompt_tokens(self, cli):
        tokens = [(Token.Username, getpass.getuser())]
        if self._tier:
            tokens.extend([(Token.At, "@"), (Token.Tier, self._tier)])
        tokens.extend([(Token.Colon, ""), (Token.Pound, "> ")])
        return tokens

    def parse_and_evaluate(self, stdout, input):
        command_parts = split_command(input)
        if command_parts and command_parts[0]:
            cmd = command_parts[0]
            args = command_parts[1] if len(command_parts) > 1 else None
            return self.evaluate_command(stdout, cmd, args, input)

    def evaluate_command(self, stdout, cmd, args, raw):
        if cmd not in self._command_registry:
            print(file=stdout)
            cprint(
                "Unknown Command '{}',{} type :help to see all "
                "available commands".format(
                    cmd, self._command_registry.find_approx(cmd)
                ),
                "magenta",
                attrs=["bold"],
                file=stdout,
            )
        else:
            if args is None:
                args = ""
            cmd_instance = self._command_registry.find_command(cmd)
            try:
                ret = self._blacklist.is_blacklisted(cmd)
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
            try:
                catchall(self._usagelogger.pre_exec)
                result = cmd_instance.run_interactive(cmd, args, raw)
                catchall(self._usagelogger.post_exec, cmd, args, result, False)
                self._status_bar.set_last_command_status(result)
                return result
            except NotImplementedError as e:
                cprint(
                    "[NOT IMPLEMENTED]: {}".format(str(e)),
                    "yellow",
                    attrs=["bold"],
                    file=stdout,
                )
                # not implemented error code
                return 99

    def run(self):
        self._cli = self._build_cli()
        stdout = self._cli.stdout_proxy(True)
        self._status_bar.start(self._cli)
        try:
            while not self.stop_requested:
                document = self._cli.run()
                text = document.text
                self.parse_and_evaluate(stdout, text)
        except (EOFError, KeyboardInterrupt):
            IOLoop.stop()

        self._status_bar.stop()

    def on_connected(self, *args, **kwargs):
        if args:
            tier = args[0]
            self._tier = tier

    @classmethod
    def stop(cls):
        cls.stop_requested = True


class ShellCompleter(Completer):
    def __init__(self, command_registry):
        super(Completer, self).__init__()
        self._command_registry = command_registry

    def get_completions(self, document, complete_event):
        if document.on_first_line:
            cmd_and_args = split_command(document.text_before_cursor)
            # are we the first word? suggest from command names
            if len(cmd_and_args) > 1:
                cmd, args = cmd_and_args
                # pass to the children
                # let's find the parent command first
                cmd_instance = self._command_registry.find_command(cmd)
                if not cmd_instance:
                    return []
                return cmd_instance.get_completions(
                    cmd,
                    Document(
                        args,
                        document.cursor_position
                        - len(document.text)
                        + len(args),
                    ),
                    complete_event,
                )
            else:
                return self._command_registry.get_completions(
                    document, complete_event
                )

        return []
