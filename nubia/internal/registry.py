#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import jellyfish

from nubia.internal.cmdbase import Command
from nubia.internal.io.eventbus import Listener

from prompt_toolkit.completion import WordCompleter

from termcolor import cprint


class CommandsRegistry:
    """
    A registry that holds all commands implementations and creates a quick
    access point for resolving a command string into the corresponding handling
    object
    """

    def __init__(self, parser, listeners):
        self._completer = WordCompleter([], ignore_case=True, sentence=True)
        # maps a command to Command Instance
        self._cmd_instance_map = {}
        # objects interested in receiving messages
        self._listeners = []
        # argparser so each command can add its options
        self._parser = parser

        for lst in listeners:
            self.register_listener(lst(self))

    def register_command(self, cmd_instance, override=False):
        if not isinstance(cmd_instance, Command):
            raise TypeError(
                "Invalid command instance, must be an instance of "
                "subclass of Command"
            )

        cmd_instance.set_command_registry(self)
        cmd_keys = cmd_instance.get_command_names()
        for cmd in cmd_keys:
            if not cmd_instance.get_help(cmd):
                cprint(
                    (
                        "[WARNING] The command {} will not be loaded. "
                        "Please provide a help message by either defining a "
                        "docstring or filling the help argument in the "
                        "@command annotation"
                    ).format(cmd_keys[0]),
                    "red",
                )
                return None

        cmd_instance.add_arguments(self._parser)

        if not override:
            conflicts = [
                cmd for cmd in cmd_keys if cmd in self._cmd_instance_map
            ]
            if conflicts:
                raise ValueError(
                    "Some other command instance has registered "
                    "the name(s) {}".format(conflicts)
                )

        if isinstance(cmd_instance, Listener):
            self._listeners.append(cmd_instance)

        for cmd in cmd_keys:
            self._cmd_instance_map[cmd.lower()] = cmd_instance
            if cmd not in self._completer.words:
                self._completer.words.append(cmd)
                self._completer.meta_dict[cmd] = cmd_instance.get_help(cmd)

        aliases = cmd_instance.get_cli_aliases()
        for alias in aliases:
            self._cmd_instance_map[alias.lower()] = cmd_instance

    def register_priority_listener(self, instance):
        """
        Registers a listener that get the top priority in callbacks
        """
        if not isinstance(instance, Listener):
            raise TypeError("Only Listeners can be registered")
        self._listeners.insert(0, instance)

    def register_listener(self, instance):
        if not isinstance(instance, Listener):
            raise TypeError("Only Listeners can be registered")
        self._listeners.append(instance)

    def __contains__(self, cmd):
        return cmd.lower() in self._cmd_instance_map

    def get_completer(self):
        return self._completer

    def get_all_commands(self):
        return set(self._cmd_instance_map.values())

    def find_command(self, cmd):
        return self._cmd_instance_map.get(cmd.lower())

    def find_approx(self, command) -> str:
        """Finds the closest command to the passed cmd, this is used in case we
        cannot find an exact match for the cmd
        """
        def are_close_enough(this, that):
            return jellyfish.damerau_levenshtein_distance(this, that) <= 2

        suggestions = [
            another_command
            for another_command in self._cmd_instance_map
            if are_close_enough(str(command), str(another_command))
        ]

        if not suggestions:
            return ""
        elif len(suggestions) == 1:
            return f" Did you mean {suggestions[0]}?"
        else:
            return f" Did you mean {', '.join(suggestions[:-1])} or {suggestions[-1]}?"

    def get_completions(self, document, complete_event):
        return self._completer.get_completions(document, complete_event)

    def dispatch_message(self, msg, *args, **kwargs):
        for mod in self._listeners:
            mod.react(msg, *args, **kwargs)

    def set_cli_args(self, args):
        self._args = args

    def get_cli_arg(self, arg):
        return getattr(self._args, arg, None)
