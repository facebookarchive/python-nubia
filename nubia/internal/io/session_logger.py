#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import re
import sys
from contextlib import contextmanager

from prompt_toolkit.patch_stdout import StdoutProxy


class SessionLogger(StdoutProxy):
    """
    SessionLogger is used to intercept stdout content and duplicates it to
    a session log file.
    """

    def __init__(self, file):
        super().__init__(raw=False)
        self._log_file = file

    def path(self):
        return self._log_file.name

    def log_command(self, cmd):
        cmd = self._strip_ansii_colors(cmd)
        self._log_file.write(f"> {cmd}\n")

    def write(self, data):
        super().write(data)
        self._log_file.write(self._strip_ansii_colors(data))

    def flush(self):
        super().flush()
        self._log_file.flush()

    def _strip_ansii_colors(self, text):
        return re.sub('\x1b\\[.+?m', '', text)

    @contextmanager
    def patch(self):
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self

        try:
            yield
        finally:
            self.flush()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
