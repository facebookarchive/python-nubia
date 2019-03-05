#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from dataclasses import dataclass


@dataclass
class Options:
    """Class for defining Nubia options and settings"""

    # File-based history is enabled by default. If this is set to false, we
    # fallback to the in-memory history.
    persistent_history: bool = True
