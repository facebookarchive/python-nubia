#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import sys
from nubia import Nubia, Options
from nubia_plugin import NubiaExamplePlugin
import example.commands

if __name__ == "__main__":
    plugin = NubiaExamplePlugin()
    shell = Nubia(
        name="nubia_example",
        command_pkgs=example.commands,
        plugin=plugin,
        options=Options(persistent_history=False),
    )
    sys.exit(shell.run())
