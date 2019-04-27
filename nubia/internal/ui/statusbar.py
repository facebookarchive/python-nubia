#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#


from nubia.internal.io import eventbus


class StatusBar(eventbus.Listener):
    def __init__(self, context):
        pass

    def on_connected(self, *args, **kwargs):
        """
        Do nothing by default.
        """
        pass

    def get_rprompt_tokens(self):
        return []

    def set_last_command_status(self, status):
        pass

    def get_tokens(self):
        return []

    def start(self):
        pass

    def stop(self):
        pass
