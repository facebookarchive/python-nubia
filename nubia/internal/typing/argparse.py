#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse
import copy
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from functools import partial
from typing import Any, Dict, List, Tuple  # noqa F401

from nubia.internal.typing.builder import (
    build_value,
    get_dict_kv_arg_type_as_str,
    get_list_arg_type_as_str,
)
from nubia.internal.typing.inspect import (
    get_first_type_argument,
    is_iterable_type,
    is_mapping_type,
    is_optional_type,
)

from . import command, inspect_object, transform_name


def create_subparser_class(opts_parser):
    # This is a hack to add the main parser arguments to each subcommand in
    # order to allow main parser arguments to be specified after the
    # subcommand, e.g.
    #    my_prog status -t <tier> --atonce=10
    #
    # The rationale of the implementation chosen is to propagate mutually
    # exclusive groups from main parser to subparsers. While it is  possible
    # to infer kwargs from main parser actions list then passing them to the
    # add_argument() method for each subparser, it will make us lose any
    # information about mutually exclusive groups.

    class SubParser(argparse.ArgumentParser):
        def __init__(self, *args, **kwargs):
            kwargs["add_help"] = False
            super(SubParser, self).__init__(*args, **kwargs)
            self._copied_actions_fingerprints = set()
            # Copy mutually exclusive groups first
            self._copy_mutually_exclusive_groups()
            # Obviously we care only about optionals
            self._copy_optionals()

        def _copy_action(self, action, group, default=argparse.SUPPRESS):
            action_fingerprint = "".join(action.option_strings)
            # Avoid adding same option twice
            if action_fingerprint not in self._copied_actions_fingerprints:
                # FIXME: this is a really, really bad idea
                a = copy.copy(action)
                # Avoid common arguments to be overridden by subnamespace
                a.default = default
                group._add_action(a)
                self._copied_actions_fingerprints.add(action_fingerprint)

        def _copy_mutually_exclusive_groups(self):
            for mutex_group in opts_parser._mutually_exclusive_groups:
                mutex_group_copy = self.add_mutually_exclusive_group(
                    required=mutex_group.required
                )

                for action in mutex_group._group_actions:
                    self._copy_action(action, mutex_group_copy)

        def _copy_optionals(self):
            for action in opts_parser._optionals._actions:
                # Skip _SubParsersAction from main parser
                if not isinstance(action, argparse._SubParsersAction):
                    self._copy_action(action, self._optionals)

    return SubParser


def add_command(argparse_parser, function):
    inspection = inspect_object(function)
    if not inspection.command:
        return add_command(argparse_parser, command(function))
    parser = register_command(argparse_parser, inspection)
    # put a back reference so we can find this function later on `find_command`
    # used in testing
    parser.__command = function
    return parser


def register_command(argparse_parser, inspection):
    _command = inspection.command
    # auto wrap the function with @command in case its not wrapped into one
    subparsers = _resolve_subparsers(argparse_parser)

    subparser = subparsers.add_parser(
        _command.name, aliases=_command.aliases, help=_command.help
    )

    # Exclusive arguments needs to be added to argparse's mutually exclusive
    # groups
    exclusive_args = _command.exclusive_arguments or []
    mutually_exclusive_groups = defaultdict(
        subparser.add_mutually_exclusive_group
    )
    for arg in inspection.arguments.values():
        add_argument_args, add_argument_kwargs = _argument_to_argparse_input(
            arg
        )
        groups = [group for group in exclusive_args if arg.name in group]

        if not groups:
            subparser.add_argument(*add_argument_args, **add_argument_kwargs)
        elif len(groups) == 1:
            me_group = mutually_exclusive_groups[groups[0]]
            me_group.add_argument(*add_argument_args, **add_argument_kwargs)
        elif len(groups) > 1:
            msg = (
                "Argument {} is present in more than one exclusive "
                "group: {}. This should not be allowed by the @command "
                "decorator".format(arg.name, groups)
            )
            raise ValueError(msg)

    # if we are adding a super command then we need to create a sub parser for
    # this
    if len(inspection.subcommands) > 0:
        subcommand_parsers = subparser.add_subparsers(
            dest="_subcmd",
            help=_command.help,
            parser_class=create_subparser_class(subparser),
            metavar="[subcommand]".format(_command.name),
        )
        subcommand_parsers.required = True
        # recursively add sub-commands
        for _, v in inspection.subcommands:
            register_command(subcommand_parsers, v)

    return subparser


def _resolve_subparsers(parser):
    # a subparser resulting from parser.add_subparsers was inputted
    if isinstance(parser, argparse._SubParsersAction):
        subparsers = parser
    # an actual parser was inputted
    elif isinstance(parser, argparse.ArgumentParser):
        # Unfortunately there is no method to get the current subparsers apart
        # from reading the private property. Trying to call
        # parser.add_subparsers a second time will result in a SystemExit error.
        # Also when you call parser.add_subparsers you get an Action object,
        # that is listed under parser._subparsers._actions.
        # Argparse is a beautiful thing
        if getattr(parser, "_subparsers", None):
            subparsers = parser._subparsers._actions[-1]
        else:
            subparsers = parser.add_subparsers(
                dest="_cmd", help="Subcommand to run"
            )
    else:
        raise ValueError(
            "Expected an argparse.ArgumentParser or an "
            "argparse._SubParsersAction as input"
        )

    return subparsers


def _argument_to_argparse_input(arg):
    # type: (Any) -> Tuple[List, Dict[str, Any]]

    add_argument_kwargs = {"help": arg.description}
    if arg.positional:
        add_argument_args = [arg.name]
        if arg.extra_names:
            msg = "Aliases are not yet supported for positional arguments @ {}".format(
                arg.name
            )
            raise ValueError(msg)
        if arg.default_value_set:
            msg = (
                "Positional arguments with default values are "
                "not supported @ {}".format(arg.name)
            )
            raise ValueError(msg)
    else:
        add_argument_args = [
            transform_argument_name(x) for x in ([arg.name] + arg.extra_names)
        ]
        add_argument_kwargs["default"] = arg.default_value
        add_argument_kwargs["required"] = not arg.default_value_set

    argument_type = (
        arg.type
        if not is_optional_type(arg.type)
        else get_first_type_argument(arg.type)
    )
    if argument_type in [int, float, str]:
        add_argument_kwargs["type"] = argument_type
        add_argument_kwargs["metavar"] = str(argument_type.__name__).upper()
    elif argument_type == bool or arg.default_value is False:
        add_argument_kwargs["action"] = "store_true"
    elif arg.default_value is True:
        add_argument_kwargs["action"] = "store_false"
    elif is_mapping_type(argument_type):
        add_argument_kwargs["type"] = _parse_dict(argument_type)
        add_argument_kwargs["metavar"] = "DICT[{}: {}]".format(
            *get_dict_kv_arg_type_as_str(argument_type)
        )
    elif is_iterable_type(argument_type):
        add_argument_kwargs["type"] = get_first_type_argument(argument_type)
        add_argument_kwargs["nargs"] = "+"
        add_argument_kwargs["metavar"] = "{}".format(
            get_list_arg_type_as_str(argument_type)
        )
    else:
        add_argument_kwargs["type"] = argument_type

    if arg.choices:
        add_argument_kwargs["choices"] = arg.choices
        add_argument_kwargs["metavar"] = "{{{}}}".format(
            ",".join(map(str, arg.choices))
        )
    if arg.positional and "metavar" in add_argument_kwargs:
        add_argument_kwargs["metavar"] = "{}<{}>".format(
            arg.name, add_argument_kwargs["metavar"]
        )

    return add_argument_args, add_argument_kwargs


def find_command(parser, parsed_args, curry_args=False):
    subparsers = _resolve_subparsers(parser)
    parser_map = dict(item for item in subparsers._name_parser_map.items())

    parser = parser_map.get(parsed_args._cmd)
    function = parser.__command if parser else None

    if not function:
        return None

    if curry_args:
        kwargs = get_arguments_for_command(function, parsed_args)
        function = partial(function, **kwargs)

    return function


def get_arguments_for_inspection(inspection, kwargs):
    # map back from names or extra names given to arguments to the actual
    # arguments taken by the function
    names_to_args = {
        transform_name(arg_obj.name, to_char="_"): arg_obj.arg
        for arg, arg_obj in inspection.arguments.items()
    }
    names_to_args.update(
        {
            transform_name(extra_name, to_char="_"): arg_obj.arg
            for arg, arg_obj in inspection.arguments.items()
            for extra_name in arg_obj.extra_names
        }
    )

    # disconsider _cmd as it is used to identify the function/parser, not the
    # actual arguments
    valid_args = set(
        map(lambda arg_obj: arg_obj.arg, inspection.arguments.values())
    )
    # use the reverse map to convert the names used in parsing to the actual
    # arguments used in the command function
    # filter out any argument that is not accepted by this function.
    kwargs = {
        names_to_args.get(name, name): value
        for name, value in kwargs.items()
        if names_to_args.get(name, name) in valid_args
    }
    return kwargs


def get_arguments_for_command(function, parsed_args):
    # map back from names or extra names given to arguments to the actual
    # arguments taken by the function
    inspection = inspect_object(function)
    kwargs = dict(parsed_args._get_kwargs())
    return get_arguments_for_inspection(inspection, kwargs)


def transform_argument_name(name):
    """
    Similar to transform_name, this is specific to export argument names
    for the cli mode. Single character friendly names are treated as flags and
    have a single dash (-) instead of a double dash (--)
    For instance:
        __special__ => --special
        _some_arg = --some-arg
        _f => -f
    """
    name = transform_name(name)
    return "--{}".format(name) if len(name) > 1 else "-{}".format(name)


def _parse_dict(target_type):
    def parse_dict_(value):
        return build_value(value, target_type, python_syntax=False)

    return parse_dict_


class NubiaHelpAction(argparse.Action):
    """An action that pipes help message to the pager."""

    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None,
    ):
        super(NubiaHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        help_message = parser.format_help()
        help_message_length = len(help_message.split("\n"))
        _, rows = shutil.get_terminal_size()
        fits_one_page = help_message_length <= rows
        if sys.stdout.isatty() and not fits_one_page:
            pager = os.environ.get("PAGER", "less")
            subprocess.run([pager], input=help_message.encode())
        else:  # fallback
            parser.print_help()
        parser.exit()
