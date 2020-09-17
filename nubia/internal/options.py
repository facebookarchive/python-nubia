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

    # Auto-executing single suggestions is enabled by default.
    #  - if there is a single prefix suggestion (unique prefix match) it automatically
    #    executes it
    #  - if there are multiple prefix suggestions, it prints a message with the
    #    suggestions
    #  - if there are no prefix suggestions, and there's a single levenshtein
    #    suggestion it automatically executes it
    #  - if there are multiple levenshtein suggestions, it prints a message with the
    #    suggestions
    # If this is set to false it just prints the suggestions
    auto_execute_single_suggestions: bool = True
