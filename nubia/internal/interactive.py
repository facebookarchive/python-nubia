#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from typing import List, Tuple, Any
import logging
import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.layout.processors import HighlightMatchingBracketProcessor
from prompt_toolkit.lexers import PygmentsLexer

from nubia.internal.ui.lexer import NubiaLexer
from termcolor import cprint

from nubia.internal.helpers import catchall
from nubia.internal.io.eventbus import Listener
from nubia.internal.options import Options
from nubia.internal.ui.style import shell_style


def split_command(text):
    return text.split(" ", 1)


class IOLoop(Listener):
    def __init__(self, context, plugin, usagelogger, options: Options):
        self._ctx = context
        self._command_registry = self._ctx.registry
        self._plugin = plugin
        self._options = options
        self._blacklist = self._plugin.getBlacklistPlugin()
        self._status_bar = self._plugin.get_status_bar(context)
        self._completer = ShellCompleter(self._command_registry)
        self._command_registry.register_listener(self)
        self._usagelogger = usagelogger

    def _build_cli(self):
        if self._options.persistent_history:
            history = FileHistory(
                os.path.join(
                    os.path.expanduser("~"), ".{}_history".format(self._ctx.binary_name)
                )
            )
        else:
            history = InMemoryHistory()

        # If EDITOR does not exist, take EMACS
        # if it does, try fit the EMACS/VI pattern using upper
        editor = getattr(
            EditingMode,
            os.environ.get("EDITOR", "EMACS").upper(),
            EditingMode.EMACS,
        )

        return PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(NubiaLexer),
            completer=self._completer,
            input_processors=[HighlightMatchingBracketProcessor(chars="[](){}")],
            style=shell_style,
            bottom_toolbar=self._get_bottom_toolbar,
            editing_mode=editor,
            complete_in_thread=True,
            refresh_interval=1,
            include_default_pygments_style=False,
        )

    def _get_prompt_tokens(self) -> List[Tuple[Any, str]]:
        return self._plugin.get_prompt_tokens(self._ctx)

    def _get_bottom_toolbar(self) -> List[Tuple[Any, str]]:
        return PygmentsTokens(self._status_bar.get_tokens())

    def parse_and_evaluate(self, input):
        command_parts = split_command(input)
        if command_parts and command_parts[0]:
            cmd = command_parts[0]
            args = command_parts[1] if len(command_parts) > 1 else None
            return self.evaluate_command(cmd, args, input)

    def evaluate_command(self, cmd, args, raw):
        if cmd not in self._command_registry:
            print()
            cprint(
                "Unknown Command '{}',{} type :help to see all "
                "available commands".format(
                    cmd, self._command_registry.find_approx(cmd)
                ),
                "magenta",
                attrs=["bold"],
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
                cprint("[NOT IMPLEMENTED]: {}".format(str(e)), "yellow", attrs=["bold"])
                # not implemented error code
                return 99

    def run(self):
        prompt = self._build_cli()
        self._status_bar.start()
        try:
            while True:
                try:
                    text = prompt.prompt(
                        PygmentsTokens(self._get_prompt_tokens()),
                        rprompt=PygmentsTokens(
                            self._status_bar.get_rprompt_tokens()
                        ),
                    )
                    self.parse_and_evaluate(text)
                except KeyboardInterrupt:
                    pass
        except EOFError:
            # Application exiting.
            pass
        self._status_bar.stop()

    def on_connected(self, *args, **kwargs):
        pass


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
                        args, document.cursor_position - len(document.text) + len(args)
                    ),
                    complete_event,
                )
            else:
                return self._command_registry.get_completions(document, complete_event)

        return []
