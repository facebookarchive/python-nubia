#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#


class CommandBlacklist:

    _blacklisted_commands = {}

    def __init__(self):
        # Ovveride this funtion
        pass

    def is_blacklisted(self, command):
        # Overide this
        return command in self._blacklisted_commands

    def add_blocked_command(self, command):
        self._blacklisted_commands[command] = ""
