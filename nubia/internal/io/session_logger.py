#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import re
import sys
import threading
from contextlib import contextmanager


class SessionLogger:
    """
    SessionLogger is used to intercept stdout content and duplicates it to
    a session log file.
    Inspired from prompt_toolkit.StdoutProxy but without the buffering.
    """

    def __init__(self, file):
        self._log_file = file
        self._lock = threading.RLock()
        self.original_stdout = sys.stdout

        # errors/encoding attribute for compatibility with sys.stdout.
        self.errors = sys.stdout.errors
        self.encoding = sys.stdout.encoding

    def path(self):
        return self._log_file.name

    def log_command(self, cmd):
        cmd = self._strip_ansii_colors(cmd)
        with self._lock:
            self._log_file.write(f"\n> {cmd}\n")

    def write(self, data):
        with self._lock:
            self.original_stdout.write(data)
            self._log_file.write(self._strip_ansii_colors(data))

    def flush(self):
        with self._lock:
            self.original_stdout.flush()
            self._log_file.flush()

    def _strip_ansii_colors(self, text):
        return re.sub("\x1b\\[.+?m", "", text)

    def isatty(self):
        return self.original_stdout.isatty()

    def fileno(self):
        return self.original_stdout.fileno()

    @contextmanager
    def patch(self):
        original_stdout = sys.stdout

        sys.stdout = self

        try:
            yield
        finally:
            self.flush()
            sys.stdout = original_stdout
