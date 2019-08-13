#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import itertools
import pyparsing as pp
from nubia.internal.helpers import function_to_str

from typing import Iterable, TYPE_CHECKING
from nubia.internal import parser
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completion

if TYPE_CHECKING:
    from nubia.internal.cmdbase import AutoCommand  # noqa


class TokenParse:
    """
    This class captures an interactive shell token that cannot be fully parser
    by the interactive shell parser and analyze it.
    """

    def __init__(self, token: str) -> None:
        self._token = token
        self._key = ""
        self._is_argument = False
        self._is_list = False
        self._is_dict = False
        self._last_value = ""
        self.parse()

    def parse(self):
        key, delim, value = self._token.partition("=")
        # Is everything before the = sane?
        if any(x in key for x in "[]{}\"'"):
            # We will treat this as positional in this case
            return

        # This is key=value
        if delim == "=":
            self._is_argument = True
            self._key = key
        else:
            # This is positional, the value is the key
            value = self._key
            assert len(value) == 0
        if len(value) > 0:
            # Let's parse the value, is it a single, list, dict?
            if value[0] == "[":
                self._is_list = True
                value = value.strip("[")
                list_values = value.rpartition(",")
                self._last_value = list_values[len(list_values) - 1].lstrip()
            elif value[0] == "{":
                self._is_dict = True
            else:
                self._last_value = value

    @property
    def is_argument(self) -> bool:
        return self._is_argument

    @property
    def is_positional(self) -> bool:
        return not self._is_argument

    # Talks about the type of the value
    @property
    def is_list(self) -> bool:
        return self._is_list

    @property
    def is_dict(self) -> bool:
        return self._is_dict

    @property
    def argument_name(self) -> str:
        assert self._is_argument
        return self._key

    def keys(self) -> Iterable[str]:
        return []

    def values(self) -> Iterable[str]:
        return []

    @property
    def last_value(self) -> str:
        return self._last_value

    @property
    def is_single_value(self) -> bool:
        return not (self._is_dict or self._is_list)


class AutoCommandCompletion:
    """
    This is the interactive completion state machine, it tracks the
    parsed tokens out of a command input and builds a data model that is
    used to understand what would be the next natural completion
    token(s).
    """

    def __init__(
        self,
        cmd_obj: "AutoCommand",
        document: Document,
        complete_event: CompleteEvent,
    ) -> None:
        self.doc = document
        self.cmd = cmd_obj
        self.meta = self.cmd.metadata
        self.event = complete_event

        # current state

    def get_completions(self) -> Iterable[Completion]:
        """
        Returns a
        """
        logger = logging.getLogger(f"{type(self).__name__}.get_completions")
        remaining = None
        try:
            parsed = parser.parse(
                self.doc.text, expect_subcommand=self.cmd.super_command
            )
        except parser.CommandParseError as e:
            parsed = e.partial_result
            remaining = e.remaining
        # This is a funky but reliable way to figure that last token we are
        # interested in manually parsing, This will return the last key=value
        # including if the value is a 'value', [list], or {dict} or combination
        # of these. This also matches positional arguments.
        if self.doc.char_before_cursor in " ]}":
            last_token = ""
        else:
            last_space = (
                self.doc.find_backwards(" ", in_current_line=True) or -1
            )
            last_token = self.doc.text[(last_space + 1) :]  # noqa
        # We pick the bigger match here. The reason we want to look into
        # remaining is to capture the state that we are in an open list,
        # dictionary, or any other value that may have spaces in it but fails
        # parsing (yet).
        if remaining and len(remaining) > len(last_token):
            last_token = remaining
        try:
            return self._prepare_args_completions(
                parsed_command=parsed, last_token=last_token
            )
        except Exception as e:
            logger.exception(str(e))
            return []

    def _prepare_args_completions(
        self, parsed_command: pp.ParseResults, last_token
    ) -> Iterable[Completion]:
        assert parsed_command is not None
        args_meta = self.meta.arguments.values()
        # are we expecting a sub command?
        if self.cmd.super_command:
            # We have a sub-command (supposedly)
            subcommand = parsed_command.get("__subcommand__")
            assert subcommand
            sub_meta = self.cmd.subcommand_metadata(subcommand)
            if not sub_meta:
                logging.debug("Parsing unknown sub-command failed!")
                return []
            # we did find the sub-command, yay!
            # In this case we chain the arguments from super and the
            # sub-command together
            args_meta = itertools.chain(args_meta, sub_meta.arguments.values())
        # Now let's see if we can figure which argument we are talking about
        args_meta = self._filter_arguments_by_prefix(last_token, args_meta)
        # Which arguments did we fully parse already? let's avoid printing them
        # in completions
        parsed_keys = parsed_command.asDict().get("kv", [])
        # We are either completing an argument name, argument value, or
        # positional value.
        # Dissect the last_token and figure what is the right completion
        parsed_token = TokenParse(last_token)
        if parsed_token.is_positional:
            # TODO: Handle positional argument completions too
            # To figure which positional we are in right now, we need to run the
            # same logic that figures if all required arguments has been
            # supplied and how many positionals have been processed and which
            # one is next.
            # This code is already in cmdbase.py run_interactive but needs to be
            # refactored to be reusable here.
            pass
        elif parsed_token.is_argument:
            argument_name = parsed_token.argument_name
            arg = self._find_argument_by_name(argument_name)
            if not arg or arg.choices in [False, None]:
                return []
            # TODO: Support dictionary keys/named tuples completion
            if parsed_token.is_dict:
                return []
            # We are completing a value, in this case, we need to get the last
            # meaninful piece of the token `x=[Tr` => `Tr`
            return [
                Completion(
                    text=str(choice),
                    start_position=-len(parsed_token.last_value),
                )
                for choice in arg.choices
                if str(choice)
                .lower()
                .startswith(parsed_token.last_value.lower())
            ]
        # We are completing arguments, or positionals.
        # TODO: We would like to only show positional choices if we exhaust all
        # required arguments. This will make it easier for the user to figure
        # that there are still required named arguments. After that point we
        # will show optional arguments and positionals as possible completions
        ret = [
            Completion(
                text=arg_meta.name + "=",
                start_position=-len(last_token),
                display_meta=self._get_arg_help(arg_meta),
            )
            for arg_meta in args_meta
            if arg_meta.name not in parsed_keys
        ]
        return ret

    def _filter_arguments_by_prefix(self, prefix: str, arguments=None):
        arguments = arguments or self.meta.arguments.values()
        if prefix:
            return [
                arg_meta
                for arg_meta in arguments
                if arg_meta.name.startswith(prefix)
            ]
        return arguments

    def _prepare_value_completions(self, prefix, partial_result):
        parsed_keys = map(lambda x: x[0], partial_result.get("kv", []))
        argument, rest = prefix.split("=", 1)
        arguments = self._filter_arguments_by_prefix(argument)
        if len(arguments) < 1:
            return []
        if len(arguments) == 1:
            argument_obj = self._find_argument_by_name(argument)
            assert argument_obj
            # was that argument used before?
            if argument in parsed_keys:
                logging.debug(
                    "Argument {} was used already, not generating "
                    "completions".format(argument)
                )
                return []
        return []

    def _find_argument_by_name(self, name):
        args_meta = list(self.meta.arguments.values())
        if self.cmd.super_command:
            # We need to get the subcommand name
            subcommand_name = self.doc.text.split(" ")[0]
            for _, sub in self.meta.subcommands:
                if sub.command.name == subcommand_name:
                    args_meta.extend(list(sub.arguments.values()))
        filtered = filter(lambda arg: arg.name == name, args_meta)
        return next(filtered, None)

    def _get_arg_help(self, arg_meta):
        sb = ["["]
        if arg_meta.type:
            sb.append(function_to_str(arg_meta.type, False, False))
            sb.append(", ")
        if arg_meta.default_value_set:
            sb.append("default: ")
            sb.append(arg_meta.default_value)
        else:
            sb.append("required")
        sb.append("] ")
        sb.append(
            arg_meta.description
            if arg_meta.description
            else "<no description provided>"
        )
        return "".join(str(item) for item in sb)
