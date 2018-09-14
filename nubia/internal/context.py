#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import copy
import sys
import os
import getpass

from nubia.internal.io.eventbus import Listener
from threading import RLock
from pygments.token import Token
from typing import List, Tuple, Any


class Context(Listener):
    def __init__(self):
        self._binary_name = None
        self._lock = RLock()
        self._testing = None
        self._registry = None
        self._args = {}

    def set_binary_name(self, name):
        self._binary_name = name

    def set_testing(self, testing):
        with self._lock:
            self._testing = testing

    def set_registry(self, registry):
        with self._lock:
            self._registry = registry

    def set_args(self, args):
        with self._lock:
            self._args = copy.deepcopy(args)

    def set_verbose(self, raw_value):
        """
        Accepts verbosity as int or True/False
        """
        try:
            value = int(raw_value)
        except ValueError:
            value = int(raw_value.lower() == "true")

        with self._lock:
            self._args.verbose = value

    @property
    def binary_name(self):
        return self._binary_name

    @property
    def testing(self):
        with self._lock:
            return self._testing

    @property
    def registry(self):
        with self._lock:
            return self._registry

    @property
    def args(self):
        with self._lock:
            return self._args

    @property
    def isatty(self):
        return os.isatty(sys.stdin.fileno())

    def get_prompt_tokens(self) -> List[Tuple[Any, str]]:
        """
        Override this and return your own prompt for interactive mode.
        Expected to return a list of pygments Token tuples.
        """
        tokens = [
            (Token.Username, getpass.getuser()),
            (Token.Colon, ""),
            (Token.Pound, "> "),
        ]
        return tokens

    def on_connected(self, *args, **kwargs):
        """
        A callback that gets called when the shell is started cli-mode,
        the args argument contains the ArgumentParser result.
        """
        pass

    def on_interactive(self, args):
        """
        A callback that gets called when the shell is started interactive-mode,
        the args argument contains the ArgumentParser result.
        """
        pass

    def on_cli(self, cmd, args):
        """
        A callback that gets called when the shell is started cli-mode,
        the args argument contains the ArgumentParser result.
        """
        pass


# This is set by LDShell class on constructor.
_ctx = None


def get_context():
    return _ctx
