#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import sys
from nubia import Nubia
from nubia_plugin import NubiaExamplePlugin

if __name__ == "__main__":
    plugin = NubiaExamplePlugin()
    shell = Nubia(name="nubia_example", plugin=plugin)
    sys.exit(shell.run())
