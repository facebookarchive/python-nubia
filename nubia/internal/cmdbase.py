#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import asyncio
import copy
import inspect
import sys
import traceback
import typing
from typing import Iterable
from collections import OrderedDict

from prompt_toolkit.completion import Completion, WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from termcolor import cprint

from . import context
from nubia.internal.completion import AutoCommandCompletion
from nubia.internal.exceptions import CommandParseError
from nubia.internal.helpers import function_to_str
from nubia.internal.helpers import issubclass_
from nubia.internal.typing import inspect_object, FunctionInspection
from nubia.internal.typing.argparse import (
    register_command,
    get_arguments_for_command,
    get_arguments_for_inspection,
)
from nubia.internal.typing.builder import apply_typing
from nubia.internal import parser

from textwrap import dedent


class Command:
    """A Command is the abstraction over one or more commands that will executed
    by the shell, A Command sub-class must implement `cmds` with a dict that
    maps command to a description.
    """

    def __init__(self):
        self._command_registry = None
        self._built_in = False

    @property
    def built_in(self) -> bool:
        return self._built_in

    def set_command_registry(self, command_registry):
        self._command_registry = command_registry

    def run_interactive(self, cmd, args, raw):
        """
        This function MUST be overridden by all commands. It will be called when
        the command is executed in interactive mode.
        """
        raise NotImplementedError("run_interactive must be overridden")

    def run_cli(self, args):
        """
        This function SHOULD be implemented in order to expose a subcommand in
        the CLI interface. It will be called when run from the CLI.
        """
        pass

    def add_arguments(self, parser):
        """
        This function receives an instance of an "argparse.ArgumentParser".
        Every command SHOULD use it to tell the CLI interface which options
        needs.
        """
        # register_command(parser, inspect_object(self._fn))
        pass

    @property
    def metadata(self) -> FunctionInspection:
        """
        Returns the command specification as an instance of FunctionInspection
        object. This is used to generate a completion model for external
        completers
        """
        return {}

    def get_completions(self, cmd, document, complete_event) -> Iterable[Completion]:
        """
        This function SHOULD be implemented to feed the interactive auto
        completion of command arguments. Example: auto complete the available
        tables in the "describe" query command.
        """
        return []

    def get_command_names(self):
        """
        This function MUST be implemented to tell the framework which commands
        this module implements. Must return a list of strings.
        """
        raise NotImplementedError("get_command_names must be overridden")

    def get_cli_aliases(self):
        """
        This function SHOULD be implemented to instruct the command dispatcher
        about alternative commands available in the CLI. Example: while the
        "commands/query.py" exports "select" and" describe" in interactive
        mode, the CLI uses the subcommand "query" to run those commands.
        Must return a list of strings.
        """
        return []

    def get_help(self, cmd, *args):
        """
        This function SHOULD be implemented to show command help when running
        ':help'. It must return a string associated with the given command.
        """
        pass

    @property
    def super_command(self) -> bool:
        """
        Does this command parse sub-commands?
        """
        return False

    def has_subcommand(self, subcommand) -> bool:
        """
        Does this command have `subcommand` as a valid sub-command?
        """
        return False


class AutoCommand(Command):
    def __init__(self, fn):
        self._built_in = False
        self._fn = fn

        if not callable(fn):
            raise ValueError("fn argument must be a callable")

        self._obj_metadata = inspect_object(fn)
        self._is_super_command = len(self.metadata.subcommands) > 0
        self._subcommand_names = []

        # We never expect a function to be passed here that has a self argument
        # In that case, we should get a bound method
        if "self" in self.metadata.arguments and not inspect.ismethod(self._fn):
            raise ValueError(
                "Expecting either a function (eg. bar) or "
                "a bound method (eg. Foo().bar). "
                "You passed what appears to be an unbound method "
                "(eg. Foo.bar) it has a 'self' argument: %s" % function_to_str(fn)
            )

        if not self.metadata.command:
            raise ValueError(
                "function or class {} needs to be annotated with "
                "@command".format(function_to_str(fn))
            )
        # If this is a super command, we need a completer for sub-commands
        if self.super_command:
            self._commands_completer = WordCompleter(
                [], ignore_case=True, sentence=True
            )
            for _, inspection in self.metadata.subcommands:
                _sub_name = inspection.command.name
                self._commands_completer.words.append(_sub_name)
                self._commands_completer.meta_dict[_sub_name] = dedent(
                    inspection.command.help
                ).strip()
                self._subcommand_names.append(_sub_name)

    @property
    def metadata(self) -> FunctionInspection:
        """
        The Inspection object of this command. This object contains all the
        information required by AutoCommand to understand the command arguments
        type information, help messages, aliases, and attributes.
        """
        return self._obj_metadata

    def _create_subcommand_obj(self, key_values):
        """
        Instantiates an object of the super command class, passes the right
        arguments and returns a dict with the remaining unused arguments
        """
        kwargs = {
            k: v
            for k, v in get_arguments_for_inspection(self.metadata, key_values).items()
            if v is not None
        }
        remaining = {k: v for k, v in key_values.items() if k not in kwargs.keys()}
        return self._fn(**kwargs), remaining

    def run_interactive(self, cmd, args, raw):
        try:
            args_metadata = self.metadata.arguments
            parsed = parser.parse(args, expect_subcommand=self.super_command)

            # prepare args dict
            parsed_dict = parsed.asDict()
            args_dict = parsed.kv.asDict()
            key_values = parsed.kv.asDict()
            command_name = cmd
            # if this is a super command, we need first to create an instance of
            # the class (fn) and pass the right arguments
            if self.super_command:
                subcommand = parsed_dict.get("__subcommand__")
                if not subcommand:
                    cprint(
                        "A sub-command must be supplied, valid values: "
                        "{}".format(", ".join(self._get_subcommands())),
                        "red",
                    )
                    return 2
                sub_inspection = self.subcommand_metadata(subcommand)
                if not sub_inspection:
                    cprint(
                        "Invalid sub-command '{}', valid values: "
                        "{}".format(subcommand, ", ".join(self._get_subcommands())),
                        "red",
                    )
                    return 2
                instance, remaining_args = self._create_subcommand_obj(args_dict)
                assert instance
                args_dict = remaining_args
                key_values = copy.copy(args_dict)
                args_metadata = sub_inspection.arguments
                attrname = self._find_subcommand_attr(subcommand)
                command_name = subcommand
                assert attrname is not None
                fn = getattr(instance, attrname)
            else:
                # not a super-command, use use the function instead
                fn = self._fn
            positionals = parsed_dict["positionals"] if parsed.positionals != "" else []
            # We only allow positionals for arguments that have positional=True
            # ِ We filter out the OrderedDict this way to ensure we don't lose the
            # order of the arguments. We also filter out arguments that have
            # been passed by name already. The order of the positional arguments
            # follows the order of the function definition.
            can_be_positional = self._positional_arguments(
                args_metadata, args_dict.keys()
            )

            if len(positionals) > len(can_be_positional):
                if len(can_be_positional) == 0:
                    err = "This command does not support positional arguments"
                else:
                    # We have more positionals than we should
                    err = (
                        "This command only supports ({}) positional arguments, "
                        "namely arguments ({}). You have passed {} arguments ({})"
                        " instead!"
                    ).format(
                        len(can_be_positional),
                        ", ".join(can_be_positional.keys()),
                        len(positionals),
                        ", ".join(str(x) for x in positionals),
                    )
                cprint(err, "red")
                return 2
            # constuct key_value dict from positional arguments.
            args_from_positionals = {
                key: value for value, key in zip(positionals, can_be_positional)
            }
            # update the total arguments dict with the positionals
            args_dict.update(args_from_positionals)

            # Run some validations on number of arguments provided

            # do we have keys that are supplied in both positionals and
            # key_value style?
            duplicate_keys = set(args_from_positionals.keys()).intersection(
                set(key_values.keys())
            )
            if duplicate_keys:
                cprint(
                    "Arguments '{}' have been passed already, cannot have"
                    " duplicate keys".format(list(duplicate_keys)),
                    "red",
                )
                return 2

            # check for verbosity override in kwargs
            ctx = context.get_context()
            old_verbose = ctx.args.verbose
            if "verbose" in args_dict:
                ctx.set_verbose(args_dict["verbose"])
                del args_dict["verbose"]
                del key_values["verbose"]

            # do we have keys that we know nothing about?
            extra_keys = set(args_dict.keys()) - set(args_metadata)
            if extra_keys:
                cprint(
                    "Unknown argument(s) {} were" " passed".format(list(extra_keys)),
                    "magenta",
                )
                return 2

            # is there any required keys that were not resolved from positionals
            # nor key_values?
            missing_keys = set(args_metadata) - set(args_dict.keys())
            if missing_keys:
                required_missing = []
                for key in missing_keys:
                    if not args_metadata[key].default_value_set:
                        required_missing.append(key)
                if required_missing:
                    cprint(
                        "Missing required argument(s) {} for command"
                        " {}".format(required_missing, command_name),
                        "yellow",
                    )
                    return 3

            # convert expected types for arguments
            for key, value in args_dict.items():
                target_type = args_metadata[key].type
                if target_type is None:
                    target_type = str
                try:
                    new_value = apply_typing(value, target_type)
                except ValueError:
                    fn_name = function_to_str(target_type, False, False)
                    cprint(
                        'Cannot convert value "{}" to {} on argument {}'.format(
                            value, fn_name, key
                        ),
                        "yellow",
                    )
                    return 4
                else:
                    args_dict[key] = new_value

            # Validate that arguments with `choices` are supplied with the
            # acceptable values.
            for arg, value in args_dict.items():
                choices = args_metadata[arg].choices
                if choices:
                    # Validate the choices in the case of values and list of
                    # values.
                    if issubclass_(args_metadata[arg].type, typing.List):
                        bad_inputs = [v for v in value if v not in choices]
                        if bad_inputs:
                            cprint(
                                f"Argument '{arg}' got an unexpected "
                                f"value(s) '{bad_inputs}'. Expected one "
                                f"or more of {choices}.",
                                "red",
                            )
                            return 4
                    elif value not in choices:
                        cprint(
                            f"Argument '{arg}' got an unexpected value "
                            f"'{value}'. Expected one of "
                            f"{choices}.",
                            "red",
                        )
                        return 4

            # arguments appear to be fine, time to run the function
            try:
                # convert argument names back to match the function signature
                args_dict = {args_metadata[k].arg: v for k, v in args_dict.items()}
                if inspect.iscoroutinefunction(fn):
                    loop = asyncio.get_event_loop()
                    ret = loop.run_until_complete(fn(**args_dict))
                else:
                    ret = fn(**args_dict)
                ctx.set_verbose(old_verbose)
            except Exception as e:
                cprint("Error running command: {}".format(str(e)), "red")
                cprint("-" * 60, "yellow")
                traceback.print_exc(file=sys.stderr)
                cprint("-" * 60, "yellow")
                return 1

            return ret

        except CommandParseError as e:
            cprint("Error parsing command", "red")
            cprint(cmd + " " + args, "white", attrs=["bold"])
            cprint((" " * (e.col + len(cmd))) + "^", "white", attrs=["bold"])
            cprint(str(e), "yellow")
            return 1

    def _positional_arguments(self, args_metadata, filter_out):
        positionals = OrderedDict()
        for k, v in args_metadata.items():
            if v.positional and k not in filter_out:
                positionals[k] = v
        return positionals

    def subcommand_metadata(self, name: str) -> FunctionInspection:
        assert self.super_command
        subcommands = self.metadata.subcommands
        for _, inspection in subcommands:
            if inspection.command.name == name:
                return inspection

    def _find_subcommand_attr(self, name):
        assert self.super_command
        subcommands = self.metadata.subcommands
        for attr, inspection in subcommands:
            if inspection.command.name == name or name in inspection.command.aliases:
                return attr
        # be explicit about returning None for readability
        return None

    def _get_subcommands(self) -> Iterable[str]:
        assert self.super_command
        return [inspection.command.name for _, inspection in self.metadata.subcommands]

    def _kwargs_for_fn(self, fn, args):
        return {
            k: v
            for k, v in get_arguments_for_command(fn, args).items()
            if v is not None
        }

    def run_cli(self, args):
        # if this is a super-command, we need to dispatch the call to the
        # correct function
        kwargs = self._kwargs_for_fn(self._fn, args)
        try:
            if self._is_super_command:
                # let's instantiate an instance of the klass
                instance = self._fn(**kwargs)
                # we need to find the actual method we want to call, in addition to
                # this we need to extract the correct kwargs for this method
                # find which function it is in the sub commands
                attrname = self._find_subcommand_attr(args._subcmd)
                assert attrname is not None
                fn = getattr(instance, attrname)
                kwargs = self._kwargs_for_fn(fn, args)
            else:
                fn = self._fn
            if inspect.iscoroutinefunction(fn):
                # execute in an event loop
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(fn(**kwargs))
            else:
                return fn(**kwargs)
        except Exception as e:
            cprint("Error running command: {}".format(str(e)), "red")
            cprint("-" * 60, "yellow")
            traceback.print_exc(file=sys.stderr)
            cprint("-" * 60, "yellow")
            return 1

    @property
    def super_command(self):
        return self._is_super_command

    def has_subcommand(self, subcommand):
        assert self.super_command
        return subcommand.lower() in self._subcommand_names

    def add_arguments(self, parser):
        register_command(parser, self.metadata)

    def get_command_names(self):
        command = self.metadata.command
        return [command.name] + command.aliases

    def get_completions(
        self, _: str, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        if self._is_super_command:
            exploded = document.text.lstrip().split(" ", 1)
            # Are we at the first word? we expect a sub-command here
            if len(exploded) <= 1:
                return self._commands_completer.get_completions(
                    document, complete_event
                )

        state_machine = AutoCommandCompletion(self, document, complete_event)
        return state_machine.get_completions()

    def get_help(self, cmd, *args):
        help = self.metadata.command.help
        return dedent(help).strip() if help else None
