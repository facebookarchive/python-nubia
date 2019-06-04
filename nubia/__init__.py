#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from .internal import context
from .internal import exceptions
from .internal.deprecation import deprecated
from .internal.io import eventbus
from .internal.ui import statusbar
from .internal.nubia import Nubia
from .internal.options import Options
from .internal.plugin_interface import PluginInterface, CompletionDataSource
from .internal.typing import argument
from .internal.typing import command

name = "nubia"

__all__ = [
    "CompletionDataSource",
    "Nubia",
    "Options",
    "PluginInterface",
    "argument",
    "command",
    "context",
    "deprecated",
    "eventbus",
    "exceptions",
    "statusbar",
]

__version__ = "0.2b1"
