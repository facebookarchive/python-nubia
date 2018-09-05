#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#


class CommandParseError(Exception):
    pass


class CommandError(Exception):
    pass


class UnknownCommand(CommandError):
    pass


class ArgsValidationError(Exception):
    pass
