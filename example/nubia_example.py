#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import asyncio
import sys

import example.commands
from nubia import Nubia, Options
from nubia_plugin import NubiaExamplePlugin


if __name__ == "__main__":
    plugin = NubiaExamplePlugin()
    shell = Nubia(
        name="nubia_example",
        command_pkgs=example.commands,
        plugin=plugin,
        options=Options(
            persistent_history=False, auto_execute_single_suggestions=False
        ),
    )
    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(shell.run()))
