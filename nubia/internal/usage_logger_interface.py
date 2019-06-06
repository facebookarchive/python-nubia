#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#


class UsageLoggerInterface:
    """
    The UsageLoggerInterface class is a way to customize nubia usage logging
    to your logging infrastructure.
    If active, the UsageLogger is notified on all command executions,
    which allows tracking of usage stats like number of command executions,
    runtimes, success rates, used parameters and more.
    """

    def __init__(self, context):
        """
        Init your logger here.
        """
        pass

    def pre_exec(self):
        """
        Called before every command execution.
        Can be used to measure how long tasks take to execute.
        """
        pass

    def post_exec(self, cmd, params, result, is_cli):
        """
        Called after every command execution.
        Use this for timing and logging the execution results.
        """
        pass
