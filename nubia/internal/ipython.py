#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import sys

from traitlets.config.loader import Config

from nubia.internal.helpers import try_await
from nubia.internal.ui.ipython import NubiaPrompt

try:
    from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
    raise Exception("IPython is not installed, cannot use IPython-based shell")


custom_locals = {}


async def start_interactive_python(plugin, registry, ctx, args):
    await try_await(ctx.on_interactive(args))
    cmds = list(registry.get_all_commands())
    for cmd in cmds:
        # TODO: This currently works for AutoCommands only, it's a hack to get
        # the command as a function, clean this up and make
        # _get_executable_function a public member.
        if hasattr(cmd, "_get_executable_function"):
            executable = cmd._get_executable_function()
            names = cmd.get_command_names()
            for name in names:
                # function names cannot have - in them
                name = name.replace("-", "_")
                custom_locals[name] = executable

    cfg = Config()
    cfg.TerminalInteractiveShell.prompts_class = NubiaPrompt
    # Custom Config
    cfg.InteractiveShellEmbed.autocall = 2
    cfg.InteractiveShellEmbed.autoawait = True

    banner = "LogDevice IPython Shell;  Python {}".format(sys.version)
    ipkwargs = {
        "config": cfg,
        "banner1": banner,
        "banner2": "\n",
        "user_ns": custom_locals,
    }
    plugin.update_ipython_kwargs(ctx=ctx, kwargs=ipkwargs)

    ipshell = InteractiveShellEmbed(**ipkwargs)
    for magic in plugin.get_magics():
        ipshell.register_magics(magic)
    ipshell()
