#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from nubia import command


@command
def example_command2():
    """
    An example command for testing purposes
    """
    return None


@command
class SuperCommand:
    """
    Super-Command Docs
    """

    @command
    def sub_command(self):
        """
        Sub-Command Docs
        """
        return None
