#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import json
import logging
from argparse import _SubParsersAction

from nubia.internal.typing import Command, FunctionInspection
from nubia.internal.typing.argparse import transform_argument_name


logger = logging.getLogger(__name__)


def _dump_command(cmd):
    assert isinstance(cmd, Command)
    return {
        # We can also add cmd.help if needed in the future
        "name": cmd.name
    }


def _dump_arguments(arguments):
    output = {"options": [], "positionals": []}
    for arg in arguments.values():
        if arg.positional:
            output["positionals"].append(
                {
                    "name": transform_argument_name(arg.name),
                    "values": list(arg.choices) if arg.choices else None,
                }
            )
        else:
            output["options"].append(
                {
                    "name": transform_argument_name(arg.name),
                    "extra_names": list(map(transform_argument_name, arg.extra_names)),
                    "expects_argument": not (
                        arg.type == bool or arg.default_value is False
                    ),
                    "default": arg.default_value,
                    "required": not arg.default_value_set,
                    "values": list(arg.choices) if arg.choices else None,
                }
            )
    return output


def _dump_subcommands(subcommands):
    return [_fn_to_dict(cmd) for _, cmd in subcommands]


def _dump_opts_parser_common(opts_parser, plugin):
    output = []
    top_level_actions = [
        action
        for action in opts_parser._actions
        if not isinstance(action, _SubParsersAction)
    ]
    for action in top_level_actions:
        option = {"extra_names": []}
        for name in action.option_strings:
            if name.startswith(opts_parser.prefix_chars * 2):
                option["name"] = name
            elif name.startswith(opts_parser.prefix_chars):
                option["extra_names"].append(name)
            else:
                # we don't know what that is!
                logger.warning(
                    "We found '%s' in option_strings of action %s", name, action
                )
        # we want to skip this particular one since it's hidden
        if option.get("name", "").startswith("--_"):
            continue
        option["expects_argument"] = True if action.type is not None else False
        option_name = option.get("name")
        if option_name:
            ds = plugin.get_completion_datasource_for_global_argument(option_name)
            if ds:
                option["values"] = ds.get_all()
        output.append(option)
    return output


def _fn_to_dict(inspection):
    cmd = _dump_command(inspection.command)
    cmd.update(_dump_arguments(inspection.arguments))
    if inspection.subcommands:
        cmd["commands"] = _dump_subcommands(inspection.subcommands)
    return cmd


def export_registry(plugin, args, opts_parser, registry):
    cmds = registry.get_all_commands()
    commands = []
    for cmd in cmds:
        if cmd.built_in:
            continue
        inspection = cmd.metadata
        if isinstance(inspection, FunctionInspection):
            commands.append(_fn_to_dict(inspection))
        else:
            logger.warning("Command %s is not instance of FunctionInspection", cmd)

    model = {
        "commands": commands,
        # This will include the shell top-level options, this will be included
        # in a future diff
        "options": _dump_opts_parser_common(opts_parser, plugin),
    }
    return json.dumps(model)
